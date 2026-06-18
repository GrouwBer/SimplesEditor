import { useState, useEffect, useRef } from 'react'
import Editor from '@monaco-editor/react'
import type { Monaco } from '@monaco-editor/react'
import { SIMPLES_LANGUAGE_ID, simplesMonarchTokens } from './simplesLang'
import { AuthProvider, useAuth } from './AuthContext'
import LoginPage from './pages/LoginPage'
import { useExecution } from './hooks/useExecution'
import { useTerminal } from './hooks/useTerminal'
import Terminal from './components/Terminal'
import { SplitPane } from './components/SplitPane'

const DEFAULT_CODE = [
  'programa exemplo_soma',
  '  inteiro a, b, resultado;',
  'inicio',
  '  leia a;',
  '  leia b;',
  '  resultado <- a + b;',
  '  escreval resultado;',
  'fim',
].join('\n')

// Registra a linguagem SIMPLES e tema escuro no Monaco
function registerSimplesLanguage(monaco: Monaco) {
  // Registra a linguagem SIMPLES com tokenizer Monarch (27 palavras reservadas)
  monaco.languages.register({ id: SIMPLES_LANGUAGE_ID })
  monaco.languages.setMonarchTokensProvider(SIMPLES_LANGUAGE_ID, simplesMonarchTokens)

  // Tema escuro customizado para SIMPLES
  monaco.editor.defineTheme('simples-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'keyword', foreground: '56b6c2', fontStyle: 'bold' },
      { token: 'number', foreground: 'd19a66' },
      { token: 'number.float', foreground: 'd19a66' },
      { token: 'string', foreground: 'e5c07b' },
      { token: 'comment', foreground: '98c379', fontStyle: 'italic' },
      { token: 'operator', foreground: 'c678dd' },
      { token: 'delimiter', foreground: 'abb2bf' },
      { token: 'identifier', foreground: 'e06c75' },
      { token: 'white', foreground: 'abb2bf' },
    ],
    colors: {
      'editor.background': '#0d1117',
      'editor.foreground': '#c9d1d9',
      'editor.lineHighlightBackground': '#161b22',
      'editor.selectionBackground': '#264f78',
      'editorCursor.foreground': '#58a6ff',
      'editorLineNumber.foreground': '#484f58',
      'editorLineNumber.activeForeground': '#c9d1d9',
    },
  })
}

function AppContent() {
  const { user, loading, signOut } = useAuth()
  const [code, setCode] = useState<string>(DEFAULT_CODE)
  const [healthStatus, setHealthStatus] = useState<string>('checking...')
  const [healthColor, setHealthColor] = useState<string>('#e2e8f0')
  const [nasmOutput, setNasmOutput] = useState<string | null>(null)
  const [wsStatus, setWsStatus] = useState<string>('conectando...')
  const [wsColor, setWsColor] = useState<string>('#f59e0b')
  const [terminalHeight, setTerminalHeight] = useState(200)
  const terminalHeightRef = useRef(terminalHeight) // ref para evitar stale closure no drag
  const isDraggingRef = useRef(false)

  // Mantem ref sincronizada com state
  useEffect(() => {
    terminalHeightRef.current = terminalHeight
  }, [terminalHeight])

  // Erro de compilacao para exibir no terminal
  const [compileError, setCompileError] = useState<string | null>(null)

  // WebSocket connection
  const wsRef = useRef<WebSocket | null>(null)
  const { state, exitCode, durationMs, sendRun, sendStop, handleMessage } = useExecution(wsRef)
  const { lines, appendOutput, sendStdin, clearTerminal } = useTerminal(wsRef)

  useEffect(() => {
    let ws: WebSocket | null = null
    let pingInterval: ReturnType<typeof setInterval> | null = null
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null
    let mounted = true

    const connect = () => {
      if (!mounted) return
      
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/run`
      
      setWsStatus('conectando...')
      setWsColor('#f59e0b')
      
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        if (!mounted) return
        console.log('[App] WebSocket conectado')
        setWsStatus('conectado')
        setWsColor('#10b981')
        wsRef.current = ws
        
        // Ping keepalive a cada 25s
        pingInterval = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, 25000)
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'pong') return
          handleMessage(msg)
          if (msg.asm) setNasmOutput(msg.asm)
          if (msg.type === 'stdout' || msg.type === 'stderr') {
            appendOutput(msg.data || '', msg.type as 'stdout' | 'stderr')
          }
          // Exibe erros de compilacao no terminal e limpa ao iniciar nova execucao
          if (msg.type === 'compile_error' || msg.type === 'assemble_error' || msg.type === 'link_error') {
            const errLine = msg.line ? `linha ${msg.line}` : ''
            const errCol = msg.column ? `, coluna ${msg.column}` : ''
            const location = errLine || errCol ? ` (${errLine}${errCol})` : ''
            setCompileError(`[${msg.type}] ${msg.message || 'erro desconhecido'}${location}`)
          }
          if (msg.type === 'internal_error') {
            setCompileError(`[Erro interno] ${msg.message || 'erro desconhecido'}`)
          }
        } catch (e) {
          console.error('[App] Erro ao processar mensagem WS:', e)
        }
      }

      ws.onclose = () => {
        if (!mounted) return
        console.log('[App] WebSocket desconectado — reconectando em 2s...')
        if (pingInterval) { clearInterval(pingInterval); pingInterval = null }
        wsRef.current = null
        setWsStatus('reconectando...')
        setWsColor('#f59e0b')
        reconnectTimeout = setTimeout(connect, 2000)
      }

      ws.onerror = () => {
        // onclose sempre dispara depois de onerror — nao precisa tratar aqui
      }
    }

    connect()

    return () => {
      mounted = false
      if (pingInterval) clearInterval(pingInterval)
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
      try { ws?.close() } catch (e) { /* ok */ }
      wsRef.current = null
    }
  }, [appendOutput, handleMessage])

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setHealthStatus('ONLINE')
          setHealthColor('#10b981')
        } else {
          setHealthStatus('UNEXPECTED')
          setHealthColor('#f59e0b')
        }
      })
      .catch(() => {
        setHealthStatus('OFFLINE')
        setHealthColor('#ef4444')
      })
  }, [])

  // Se estiver carregando a sessao, mostra tela de loading
  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#0b0f19',
        color: '#6b7280',
        fontFamily: 'Inter, system-ui, sans-serif',
      }}>
        Carregando...
      </div>
    )
  }

  // Se nao estiver autenticado, mostra tela de login
  if (!user) {
    return <LoginPage />
  }

  // Callback executado antes do Monaco montar
  const handleBeforeMount = (monaco: Monaco) => {
    registerSimplesLanguage(monaco)
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0b0f19',
      color: '#f3f4f6',
      fontFamily: 'Inter, system-ui, sans-serif',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.5rem 1rem',
        borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
        backgroundColor: 'rgba(17, 24, 39, 0.8)',
        backdropFilter: 'blur(8px)',
        flexShrink: 0,
      }}>
        <h1 style={{
          fontSize: '1rem',
          fontWeight: 700,
          margin: 0,
          background: 'linear-gradient(135deg, #a5b4fc 0%, #6366f1 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          SIMPLES Editor
        </h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {(state === 'idle' || state === 'finished') && (
            <button
              onClick={() => { setCompileError(null); setNasmOutput(null); wsStatus === 'conectado' && sendRun(code) }}
              disabled={wsStatus !== 'conectado'}
              title={wsStatus !== 'conectado' ? `WebSocket ${wsStatus} — aguarde conectar` : 'Executar codigo'}
              style={{
                padding: '4px 12px',
                fontSize: '0.75rem',
                fontWeight: 600,
                borderRadius: '4px',
                border: 'none',
                cursor: wsStatus === 'conectado' ? 'pointer' : 'not-allowed',
                backgroundColor: state === 'finished' ? '#059669'
                  : wsStatus === 'conectado' ? '#6366f1'
                  : '#374151',
                color: wsStatus === 'conectado' ? '#fff' : '#6b7280',
                opacity: wsStatus === 'conectado' ? 1 : 0.6,
              }}
            >
              {wsStatus === 'conectado'
                ? (state === 'finished' ? 'EXECUTAR NOVAMENTE' : 'EXECUTAR')
                : `WS: ${wsStatus}...`
              }
            </button>
          )}
          {state === 'compiling' && (
            <span style={{ fontSize: '0.75rem', color: '#f59e0b' }}>Compilando...</span>
          )}
          {state === 'executing' && (
            <button
              onClick={sendStop}
              style={{
                padding: '4px 12px',
                fontSize: '0.75rem',
                fontWeight: 600,
                borderRadius: '4px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: '#ef4444',
                color: '#fff',
              }}
            >
              PARAR
            </button>
          )}
          {user && (
            <>
              <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                {user.email}
              </span>
              <button
                onClick={signOut}
                style={{
                  padding: '2px 8px',
                  fontSize: '0.7rem',
                  borderRadius: '4px',
                  border: '1px solid rgba(255,255,255,0.1)',
                  cursor: 'pointer',
                  backgroundColor: 'transparent',
                  color: '#9ca3af',
                }}
              >
                Sair
              </button>
            </>
          )}
          <span style={{
            display: 'inline-block',
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: healthColor,
            boxShadow: `0 0 6px ${healthColor}`,
          }} />
          <span style={{ fontSize: '0.75rem', color: '#9ca3af', fontWeight: 500 }}>
            API: {healthStatus}
          </span>
          <span style={{
            display: 'inline-block',
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: wsColor,
            boxShadow: `0 0 6px ${wsColor}`,
            marginLeft: '4px',
          }} />
          <span style={{ fontSize: '0.75rem', color: '#9ca3af', fontWeight: 500 }}>
            WS: {wsStatus}
          </span>
        </div>
      </header>

      {/* Main + Terminal: Split vertical */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Editor + NASM: SplitPane horizontal */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>
          <SplitPane defaultLeftWidth={60} minLeftWidth={30} minRightWidth={20}>
            {/* Code Editor */}
            <section style={{
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
            }}>
              <div style={{
                padding: '0.35rem 1rem',
                fontSize: '0.7rem',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                color: '#6b7280',
                borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                backgroundColor: 'rgba(17, 24, 39, 0.6)',
                flexShrink: 0,
              }}>
                Editor (SIMPLES)
              </div>
              <div style={{ flex: 1 }}>
                <Editor
                  height="100%"
                  language={SIMPLES_LANGUAGE_ID}
                  value={code}
                  onChange={value => setCode(value ?? '')}
                  theme="simples-dark"
                  beforeMount={handleBeforeMount}
                  options={{
                    fontSize: 14,
                    fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
                    minimap: { enabled: false },
                    lineNumbers: 'on',
                    renderWhitespace: 'selection',
                    tabSize: 4,
                    wordWrap: 'off',
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                  }}
                />
              </div>
            </section>

            {/* NASM Output panel */}
            <aside style={{
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
              backgroundColor: 'rgba(17, 24, 39, 0.4)',
            }}>
              <div style={{
                padding: '0.35rem 1rem',
                fontSize: '0.7rem',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                color: '#6b7280',
                borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                backgroundColor: 'rgba(17, 24, 39, 0.6)',
                flexShrink: 0,
              }}>
                NASM Output
              </div>
              <div style={{
                flex: 1,
                padding: '1rem',
                color: nasmOutput ? '#e2e8f0' : '#4b5563',
                fontSize: '0.85rem',
                fontFamily: "'JetBrains Mono', monospace",
                overflow: 'auto',
                whiteSpace: 'pre-wrap',
              }}>
                {nasmOutput || (
                  <p style={{ textAlign: 'center', lineHeight: 1.6 }}>
                    O codigo assembly gerado aparecera aqui<br />
                    <span style={{ fontSize: '0.75rem' }}>(Clique em EXECUTAR para compilar)</span>
                  </p>
                )}
              </div>
            </aside>
          </SplitPane>
        </div>

        {/* Divisor vertical do terminal — arrastavel para redimensionar */}
        <div
          onMouseDown={(e) => {
            e.preventDefault()
            e.stopPropagation()
            isDraggingRef.current = true
            const startY = e.clientY
            const startHeight = terminalHeightRef.current
            const onMove = (ev: MouseEvent) => {
              if (!isDraggingRef.current) return
              const delta = startY - ev.clientY
              const newHeight = Math.max(80, Math.min(window.innerHeight * 0.7, startHeight + delta))
              setTerminalHeight(newHeight)
            }
            const onUp = () => {
              isDraggingRef.current = false
              document.removeEventListener('mousemove', onMove)
              document.removeEventListener('mouseup', onUp)
              document.body.style.userSelect = ''
              document.body.style.cursor = ''
            }
            document.addEventListener('mousemove', onMove)
            document.addEventListener('mouseup', onUp)
            document.body.style.userSelect = 'none'
            document.body.style.cursor = 'row-resize'
          }}
          style={{
            height: '12px',
            cursor: 'row-resize',
            backgroundColor: 'rgba(255, 255, 255, 0.06)',
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background-color 0.15s',
            position: 'relative',
            zIndex: 10,
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLElement).style.backgroundColor = 'rgba(99, 102, 241, 0.15)'
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLElement).style.backgroundColor = 'rgba(255, 255, 255, 0.06)'
          }}
        >
          <div style={{
            width: '48px',
            height: '5px',
            borderRadius: '3px',
            backgroundColor: 'rgba(255, 255, 255, 0.15)',
          }} />
        </div>

        {/* Terminal resizable */}
        <div style={{
          height: `${terminalHeight}px`,
          flexShrink: 0,
        }}>
          <Terminal
            lines={lines}
            execState={state}
            exitCode={exitCode}
            durationMs={durationMs}
            compileError={compileError}
            onSendStdin={sendStdin}
            onClear={() => { clearTerminal(); setCompileError(null) }}
          />
        </div>
      </div>

      {/* Footer */}
      <footer style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.4rem 1rem',
        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
        backgroundColor: 'rgba(17, 24, 39, 0.8)',
        fontSize: '0.7rem',
        color: '#4b5563',
        flexShrink: 0,
      }}>
        <span>SIMPLES Editor v0.3.0</span>
        <span>{code.split('\n').length} linhas</span>
      </footer>

      {/* Keyframes para animacao do spinner */}
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
