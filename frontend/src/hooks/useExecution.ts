import { useState, useCallback, useRef } from 'react'

// Tipos do protocolo WebSocket (PRD secao 9.2)
export interface WsMessage {
  type: string
  data?: string
  asm?: string
  line?: number
  column?: number
  message?: string
  exit_code?: number
  duration_ms?: number
  limit_s?: number
  code?: string  // codigo fonte enviado para compilar
}

// Estados da maquina de execucao (PRD secao 12.3)
export type ExecutionState = 'idle' | 'compiling' | 'executing' | 'finished'

// Tempo maximo para o Stop (SIGTERM → SIGKILL)
const STOP_HARD_MS = 2000    // 2s maximo total (criterio de aceite)

interface StopCommand {
  type: 'stop'
}

/**
 * Hook que gerencia o estado de execucao e o envio do comando Stop.
 *
 * Implementa RF13: Stop envia SIGTERM ao processo, depois SIGKILL apos 1s.
 * Implementa criterio de aceite: Stop interrompe execucao em ≤ 2s.
 *
 * Uso:
 *   const { state, sendStop, sendRun } = useExecution(websocket)
 */
export function useExecution(wsRef: React.MutableRefObject<WebSocket | null>) {
  const [state, setState] = useState<ExecutionState>('idle')
  const [exitCode, setExitCode] = useState<number | null>(null)
  const [durationMs, setDurationMs] = useState<number | null>(null)
  const stopTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const clearStopTimer = useCallback(() => {
    if (stopTimerRef.current !== null) {
      clearTimeout(stopTimerRef.current)
      stopTimerRef.current = null
    }
  }, [])

  // Envia comando de compilacao e execucao
  const sendRun = useCallback((code: string) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn('[useExecution] WebSocket nao conectado')
      return
    }

    setState('compiling')
    setExitCode(null)
    setDurationMs(null)
    clearStopTimer()

    ws.send(JSON.stringify({ type: 'compile_and_run', code }))
  }, [wsRef, clearStopTimer])

  // Envia comando Stop (RF13)
  const sendStop = useCallback(() => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn('[useExecution] WebSocket nao conectado para enviar Stop')
      return
    }

    // Envia {type: "stop"} ao backend
    const stopMsg: StopCommand = { type: 'stop' }
    ws.send(JSON.stringify(stopMsg))

    // Timeout de seguranca: se o backend nao responder em 2s,
    // considera que a execucao foi interrompida de qualquer forma
    stopTimerRef.current = setTimeout(() => {
      console.warn('[useExecution] Stop timeout — forcando estado idle')
      setState('idle')
      setExitCode(-9) // SIGKILL
    }, STOP_HARD_MS)
  }, [wsRef])

  // Processa mensagens do WebSocket e atualiza o estado
  const handleMessage = useCallback((msg: WsMessage) => {
    switch (msg.type) {
      case 'compile_started':
        setState('compiling')
        break

      case 'asm_generated':
        // Ainda compilando (montagem + link)
        break

      case 'exec_started':
        setState('executing')
        break

      case 'compile_error':
      case 'assemble_error':
      case 'link_error':
        setState('idle')
        setExitCode(null)
        break

      case 'exit':
        clearStopTimer()
        setState('finished')
        if (typeof msg.exit_code === 'number') {
          setExitCode(msg.exit_code)
        }
        if (typeof msg.duration_ms === 'number') {
          setDurationMs(msg.duration_ms)
        }
        // Volta para idle apos exibir resultado
        setTimeout(() => setState('idle'), 3000)
        break

      case 'timeout':
        clearStopTimer()
        setState('finished')
        setExitCode(-1) // timeout
        if (typeof msg.limit_s === 'number') {
          setDurationMs(msg.limit_s * 1000)
        }
        setTimeout(() => setState('idle'), 3000)
        break

      case 'stdout':
      case 'stderr':
        // Mantem estado atual, apenas streaming de dados
        break

      case 'internal_error':
        clearStopTimer()
        setState('idle')
        break

      default:
        break
    }
  }, [clearStopTimer])

  return {
    state,
    exitCode,
    durationMs,
    sendRun,
    sendStop,
    handleMessage,
    setState,
  }
}
