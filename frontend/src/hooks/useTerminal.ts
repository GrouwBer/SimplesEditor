import { useEffect, useRef, useCallback, useState } from 'react'
import { Terminal as XTerm } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

// Estados do terminal conectado ao sandbox
export type TerminalState =
  | 'idle'
  | 'connecting'
  | 'connected'
  | 'running'
  | 'error'

interface UseTerminalOptions {
  wsUrl: string
  onStateChange?: (state: TerminalState) => void
}

interface UseTerminalReturn {
  terminalRef: React.RefCallback<HTMLDivElement>
  state: TerminalState
  send: (data: string) => void
  run: (code: string) => void
  stop: () => void
  clear: () => void
}

export function useTerminal(options: UseTerminalOptions): UseTerminalReturn {
  const { wsUrl, onStateChange } = options
  const [state, setState] = useState<TerminalState>('idle')
  const xtermRef = useRef<XTerm | null>(null)
  const fitAddonRef = useRef<FitAddon | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)

  const updateState = useCallback(
    (newState: TerminalState) => {
      setState(newState)
      onStateChange?.(newState)
    },
    [onStateChange]
  )

  // Conecta WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    updateState('connecting')

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      updateState('connected')
    }

    ws.onmessage = (event: MessageEvent) => {
      try {
        const msg = JSON.parse(event.data as string) as {
          type: string
          data?: string
          code?: number
          duration_ms?: number
          asm?: string
          phase?: string
          line?: number
          column?: number
          message?: string
        }

        switch (msg.type) {
          case 'compile_started':
            xtermRef.current?.writeln('\x1b[33m[Compilando...]\x1b[0m')
            updateState('running')
            break
          case 'compile_error':
            xtermRef.current?.writeln(
              `\x1b[31m[Erro] Linha ${msg.line ?? '?'}, Coluna ${msg.column ?? '?'}: ${msg.message ?? 'erro desconhecido'}\x1b[0m`
            )
            updateState('error')
            break
          case 'asm_generated':
            xtermRef.current?.writeln('\x1b[32m[NASM gerado]\x1b[0m')
            if (msg.asm) {
              xtermRef.current?.writeln(msg.asm)
            }
            break
          case 'exec_started':
            xtermRef.current?.writeln('\x1b[36m[Executando...]\x1b[0m')
            updateState('running')
            break
          case 'stdout':
            if (msg.data) {
              xtermRef.current?.write(msg.data)
            }
            break
          case 'stderr':
            if (msg.data) {
              xtermRef.current?.write(`\x1b[31m${msg.data}\x1b[0m`)
            }
            break
          case 'exit':
            xtermRef.current?.writeln(
              `\n\x1b[90m[Programa finalizado, codigo: ${msg.code ?? 0}, duracao: ${msg.duration_ms ?? 0}ms]\x1b[0m`
            )
            updateState('connected')
            break
          case 'timeout':
            xtermRef.current?.writeln('\n\x1b[31m[Tempo limite excedido]\x1b[0m')
            updateState('connected')
            break
          case 'stdin_prompt':
            // Backend solicita input — terminal já está pronto para receber
            break
        }
      } catch {
        // Mensagem não-JSON (raw stdout/stderr)
        xtermRef.current?.write(event.data as string)
      }
    }

    ws.onerror = () => {
      xtermRef.current?.writeln('\x1b[31m[Erro na conexao WebSocket]\x1b[0m')
      updateState('error')
    }

    ws.onclose = () => {
      wsRef.current = null
      if (state !== 'error') {
        updateState('idle')
      }
    }
  }, [wsUrl, updateState, state])

  // Callback para o container do terminal
  const terminalRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (!node || xtermRef.current) return
      containerRef.current = node

      const term = new XTerm({
        theme: {
          background: '#0d1117',
          foreground: '#c9d1d9',
          cursor: '#58a6ff',
          selectionBackground: '#264f78',
          black: '#484f58',
          red: '#ff7b72',
          green: '#3fb950',
          yellow: '#d29922',
          blue: '#58a6ff',
          magenta: '#bc8cff',
          cyan: '#39c5d6',
          white: '#b1bac4',
          brightBlack: '#6e7681',
          brightRed: '#ffa198',
          brightGreen: '#56d364',
          brightYellow: '#e3b341',
          brightBlue: '#79c0ff',
          brightMagenta: '#d2a8ff',
          brightCyan: '#56d4dd',
          brightWhite: '#f0f6fc',
        },
        fontSize: 14,
        fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
        cursorBlink: true,
        allowProposedApi: true,
        scrollback: 5000,
        cols: 80,
        rows: 24,
      })

      const fitAddon = new FitAddon()
      term.loadAddon(fitAddon)
      fitAddonRef.current = fitAddon

      term.open(node)
      fitAddon.fit()

      // Envia input do teclado via WebSocket
      term.onData((data: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN && state === 'running') {
          wsRef.current.send(
            JSON.stringify({ type: 'stdin', data })
          )
        }
        // Sempre escreve no terminal local para feedback visual
        term.write(data)
      })

      // Resize handler
      const handleResize = () => {
        fitAddon.fit()
      }
      window.addEventListener('resize', handleResize)
      const observer = new ResizeObserver(() => {
        fitAddon.fit()
      })
      observer.observe(node)

      xtermRef.current = term

      // Conecta WebSocket ao montar
      connect()

      return () => {
        window.removeEventListener('resize', handleResize)
        observer.disconnect()
      }
    },
    [connect, state]
  )

  // Envia dados para o WebSocket
  const send = useCallback((data: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data)
    }
  }, [])

  // Envia código para compilação + execução
  const run = useCallback(
    (code: string) => {
      if (wsRef.current?.readyState !== WebSocket.OPEN) {
        connect()
        // Aguarda conexão e envia
        const checkAndSend = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            clearInterval(checkAndSend)
            wsRef.current!.send(
              JSON.stringify({ type: 'compile_and_run', code })
            )
          }
        }, 100)
        // Timeout após 5s
        setTimeout(() => clearInterval(checkAndSend), 5000)
        return
      }
      xtermRef.current?.clear()
      wsRef.current.send(
        JSON.stringify({ type: 'compile_and_run', code })
      )
    },
    [connect]
  )

  // Envia sinal de stop
  const stop = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'stop' }))
      xtermRef.current?.writeln('\n\x1b[33m[Enviando sinal de parada...]\x1b[0m')
    }
  }, [])

  // Limpa o terminal
  const clear = useCallback(() => {
    xtermRef.current?.clear()
  }, [])

  // Cleanup ao desmontar
  useEffect(() => {
    return () => {
      wsRef.current?.close()
      xtermRef.current?.dispose()
    }
  }, [])

  return {
    terminalRef,
    state,
    send,
    run,
    stop,
    clear,
  }
}
