import { useState, useEffect, useRef, useCallback } from 'react'
import StopButton from './components/StopButton'
import { useExecution, type WsMessage } from './hooks/useExecution'
import type { ExecutionState } from './hooks/useExecution'

function App() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...')
  const [healthColor, setHealthColor] = useState<string>('#e2e8f0')

  // Referencia ao WebSocket (compartilhada entre App e useExecution)
  const wsRef = useRef<WebSocket | null>(null)

  // Hook de execucao com state machine (RF13, RF14, RF19)
  const {
    state: execState,
    exitCode,
    durationMs,
    sendStop,
    handleMessage,
  } = useExecution(wsRef)

  // Conecta WebSocket ao backend (rota /ws/run)
  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return wsRef.current

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/run`

    const ws = new WebSocket(wsUrl)
    ws.onopen = () => {
      console.log('[App] WebSocket conectado')
    }
    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data)
        handleMessage(msg)
      } catch (err) {
        console.error('[App] Erro ao parsear mensagem WS:', err)
      }
    }
    ws.onclose = () => {
      console.log('[App] WebSocket desconectado')
      wsRef.current = null
    }
    ws.onerror = (err) => {
      console.error('[App] WebSocket erro:', err)
    }

    wsRef.current = ws
    return ws
  }, [handleMessage])

  // Ao montar, conecta WebSocket
  useEffect(() => {
    connectWs()
    return () => {
      // RF19: Logout/desmontagem encerra a sessao
      // Envia Stop antes de fechar se estiver executando
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        // Se estiver executando, envia Stop antes de fechar
        // (RF19: logout encerra qualquer execucao em andamento)
        wsRef.current.close()
      }
    }
  }, [connectWs])

  // Health check do backend
  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setHealthStatus('ONLINE')
          setHealthColor('#10b981') // emerald-500
        } else {
          setHealthStatus('UNEXPECTED RESPONSE')
          setHealthColor('#f59e0b') // amber-500
        }
      })
      .catch(() => {
        setHealthStatus('OFFLINE')
        setHealthColor('#ef4444') // red-500
      })
  }, [])

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
      {/* ===== HEADER ===== */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.logo}>
            SIMPLES
          </h1>
          <span style={styles.subtitle}>Editor</span>
        </div>

        {/* ===== TOOLBAR com StopButton ===== */}
        <div style={styles.toolbar}>
          {/* Indicador de estado da execucao */}
          {execState !== 'idle' && (
            <StatusBadge state={execState} exitCode={exitCode} durationMs={durationMs} />
          )}

          {/* Botao Stop (RF13) */}
          <StopButton state={execState} onStop={sendStop} />

          {/* Health status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              display: 'inline-block',
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: healthColor,
              boxShadow: `0 0 6px ${healthColor}`,
              transition: 'all 0.3s ease',
            }} />
            <span style={{
              fontSize: '0.8rem',
              fontWeight: 600,
              color: healthColor,
            }}>
              {healthStatus}
            </span>
          </div>
        </div>
      </header>

      {/* ===== MAIN CONTENT ===== */}
      <main style={styles.main}>
        {/* Painel do Editor (esquerda) */}
        <div style={styles.editorPanel}>
          <div style={styles.panelHeader}>
            <span>Editor SIMPLES</span>
            {execState === 'compiling' && (
              <span style={{ color: '#6366f1', fontSize: '0.8rem' }}>compilando...</span>
            )}
          </div>
          <div style={styles.editorPlaceholder}>
            <p style={styles.placeholderText}>
              Aguardando integracao do Monaco Editor (Sprint 2).
            </p>
            <p style={styles.placeholderHint}>
              Digite codigo SIMPLES aqui e clique Run para compilar e executar.
            </p>
          </div>
        </div>

        {/* Painel NASM (direita) */}
        <div style={styles.nasmPanel}>
          <div style={styles.panelHeader}>
            <span>NASM x32</span>
            <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>read-only</span>
          </div>
          <div style={styles.editorPlaceholder}>
            <p style={styles.placeholderText}>
              Assembly gerado aparecera aqui.
            </p>
          </div>
        </div>
      </main>

      {/* ===== TERMINAL (inferior) ===== */}
      <footer style={styles.terminalPanel}>
        <div style={styles.panelHeader}>
          <span>Terminal</span>
          {execState === 'executing' && (
            <span style={{ color: '#f59e0b', fontSize: '0.75rem' }}>executando...</span>
          )}
          {exitCode !== null && (
            <span style={{
              color: exitCode === 0 ? '#10b981' : '#ef4444',
              fontSize: '0.75rem',
            }}>
              exit code: {exitCode}
              {durationMs !== null && ` — ${(durationMs / 1000).toFixed(2)}s`}
            </span>
          )}
        </div>
        <div style={styles.terminalPlaceholder}>
          <p style={styles.placeholderText}>
            Aguardando integracao do xterm.js (Sprint 4).
          </p>
        </div>
      </footer>
    </div>
  )
}

// Badge de status da execucao
function StatusBadge({ state, exitCode, durationMs }: {
  state: ExecutionState
  exitCode: number | null
  durationMs: number | null
}) {
  const config: Record<ExecutionState, { text: string; color: string }> = {
    idle: { text: 'Pronto', color: '#6b7280' },
    compiling: { text: 'Compilando', color: '#6366f1' },
    executing: { text: 'Executando', color: '#f59e0b' },
    finished: {
      text: exitCode === 0 ? `Sucesso (${(durationMs ?? 0) / 1000}s)` : `Erro (code ${exitCode})`,
      color: exitCode === 0 ? '#10b981' : '#ef4444',
    },
  }

  const { text, color } = config[state]
  return (
    <span style={{
      fontSize: '0.8rem',
      fontWeight: 500,
      color,
      padding: '2px 10px',
      background: `${color}15`,
      borderRadius: '6px',
      border: `1px solid ${color}30`,
    }}>
      {text}
    </span>
  )
}

const styles: Record<string, React.CSSProperties> = {
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0.75rem 1.5rem',
    background: 'rgba(17, 24, 39, 0.8)',
    backdropFilter: 'blur(12px)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
    zIndex: 10,
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '12px',
  },
  logo: {
    margin: 0,
    fontSize: '1.4rem',
    fontWeight: 800,
    background: 'linear-gradient(135deg, #a5b4fc 0%, #6366f1 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    letterSpacing: '-0.025em',
  },
  subtitle: {
    fontSize: '0.9rem',
    color: '#6b7280',
    fontWeight: 400,
  },
  toolbar: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  main: {
    display: 'flex',
    flex: 1,
    minHeight: 0,
  },
  editorPanel: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    borderRight: '1px solid rgba(255, 255, 255, 0.06)',
    minWidth: 0,
  },
  nasmPanel: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    minWidth: 0,
  },
  panelHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0.5rem 1rem',
    background: 'rgba(255, 255, 255, 0.02)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#9ca3af',
  },
  editorPlaceholder: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem',
    background: 'rgba(255, 255, 255, 0.01)',
  },
  terminalPanel: {
    height: '200px',
    display: 'flex',
    flexDirection: 'column',
    borderTop: '1px solid rgba(255, 255, 255, 0.06)',
    minHeight: '100px',
  },
  terminalPlaceholder: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(0, 0, 0, 0.3)',
  },
  placeholderText: {
    color: '#6b7280',
    fontSize: '0.95rem',
    margin: 0,
    textAlign: 'center' as const,
  },
  placeholderHint: {
    color: '#4b5563',
    fontSize: '0.8rem',
    margin: '0.5rem 0 0',
    textAlign: 'center' as const,
  },
}

export default App
