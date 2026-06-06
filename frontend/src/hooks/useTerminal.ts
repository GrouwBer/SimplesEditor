import { useState, useCallback, useRef } from 'react'

export interface TerminalLine {
  id: number
  text: string
  type: 'stdout' | 'stderr' | 'stdin'   // stdin = o que o usuario digitou
  timestamp: number
}

/**
 * Hook que gerencia o buffer do terminal interativo.
 *
 * RF11: stdout/stderr recebido via WebSocket e exibido em tempo real.
 * RF12: Usuario digita no terminal → stdin enviado ao backend.
 *
 * Uso:
 *   const { lines, sendStdin, appendOutput } = useTerminal(wsRef)
 */
export function useTerminal(wsRef: React.MutableRefObject<WebSocket | null>) {
  const [lines, setLines] = useState<TerminalLine[]>([])
  const nextId = useRef(1)

  // Adiciona uma linha de output (stdout/stderr) ao buffer
  const appendOutput = useCallback((text: string, type: 'stdout' | 'stderr' = 'stdout') => {
    const id = nextId.current++
    setLines(prev => [...prev, { id, text, type, timestamp: Date.now() }])
  }, [])

  // Envia input do usuario para o stdin do binario (RF12)
  const sendStdin = useCallback((data: string) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.warn('[useTerminal] WebSocket nao conectado para enviar stdin')
      return false
    }

    // Adiciona nova linha se o usuario nao incluiu
    const stdinData = data.endsWith('\n') ? data : data + '\n'

    // Envia {type: "stdin", data: "..."} ao backend
    ws.send(JSON.stringify({ type: 'stdin', data: stdinData }))

    // Registra o input no historico do terminal
    const id = nextId.current++
    setLines(prev => [...prev, {
      id,
      text: data,
      type: 'stdin',
      timestamp: Date.now(),
    }])

    return true
  }, [wsRef])

  // Limpa o buffer do terminal
  const clearTerminal = useCallback(() => {
    setLines([])
    nextId.current = 1
  }, [])

  return {
    lines,
    appendOutput,
    sendStdin,
    clearTerminal,
  }
}
