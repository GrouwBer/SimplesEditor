import { useState, useEffect, useRef, useCallback } from 'react'
import { TerminalPanel, useTerminal } from './components/Terminal'

// Constantes do WebSocket — usa o mesmo host, path /ws/run
const WS_URL = `ws://${window.location.host}/ws/run`

function App() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...')
  const [healthColor, setHealthColor] = useState<string>('#e2e8f0')
  const [code, setCode] = useState<string>(
    'programa exemplo\n  inteiro x\ninicio\n  leia x\n  escreval x\nfim'
  )
  const [terminalState, setTerminalState] = useState<string>('idle')

  // Referencia as funcoes do hook useTerminal
  const terminalControl = useRef<ReturnType<typeof useTerminal> | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setHealthStatus('ONLINE')
          setHealthColor('#10b981')
        } else {
          setHealthStatus('UNEXPECTED RESPONSE')
          setHealthColor('#f59e0b')
        }
      })
      .catch(() => {
        setHealthStatus('OFFLINE')
        setHealthColor('#ef4444')
      })
  }, [])

  const handleRun = useCallback(() => {
    terminalControl.current?.run(code)
  }, [code])

  const handleStop = useCallback(() => {
    terminalControl.current?.stop()
  }, [])

  const handleClear = useCallback(() => {
    terminalControl.current?.clear()
  }, [])

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0b0f19',
      color: '#f3f4f6',
      fontFamily: 'Inter, system-ui, sans-serif',
      display: 'flex',
      flexDirection: 'column',
      padding: '1rem',
      gap: '1rem',
    }}>
      {/* Header */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.5rem 1rem',
        background: 'rgba(17, 24, 39, 0.8)',
        borderRadius: '8px',
        border: '1px solid rgba(255, 255, 255, 0.08)',
      }}>
        <h1 style={{
          fontSize: '1.5rem',
          fontWeight: 800,
          margin: 0,
          background: 'linear-gradient(135deg, #a5b4fc 0%, #6366f1 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          SIMPLES Editor
        </h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            display: 'inline-block',
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: healthColor,
            boxShadow: `0 0 6px ${healthColor}`,
          }} />
          <span style={{ fontSize: '0.85rem', color: healthColor, fontWeight: 600 }}>
            {healthStatus}
          </span>
          <span style={{ fontSize: '0.8rem', color: '#6b7280', marginLeft: '8px' }}>
            Terminal: {terminalState}
          </span>
        </div>
      </header>

      {/* Main layout: Editor + Terminal */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        minHeight: 0,
      }}>
        {/* Toolbar */}
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          alignItems: 'center',
        }}>
          <button
            onClick={handleRun}
            disabled={terminalState === 'running' || terminalState === 'connecting'}
            style={{
              padding: '0.5rem 1.5rem',
              background: terminalState === 'running'
                ? '#374151'
                : 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 600,
              cursor: terminalState === 'running' ? 'not-allowed' : 'pointer',
              fontSize: '0.9rem',
            }}
          >
            {terminalState === 'running' ? 'Executando...' : '▶ Run'}
          </button>
          <button
            onClick={handleStop}
            disabled={terminalState !== 'running'}
            style={{
              padding: '0.5rem 1.5rem',
              background: terminalState === 'running'
                ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
                : '#374151',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 600,
              cursor: terminalState === 'running' ? 'pointer' : 'not-allowed',
              fontSize: '0.9rem',
            }}
          >
            ■ Stop
          </button>
          <button
            onClick={handleClear}
            style={{
              padding: '0.5rem 1rem',
              background: 'rgba(255, 255, 255, 0.05)',
              color: '#9ca3af',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.85rem',
            }}
          >
            Limpar
          </button>
        </div>

        {/* Editor (textarea temporario ate Monaco ser integrado — issue #11) */}
        <div style={{
          flex: '0 0 auto',
          minHeight: '150px',
          maxHeight: '300px',
        }}>
          <textarea
            value={code}
            onChange={e => setCode(e.target.value)}
            spellCheck={false}
            style={{
              width: '100%',
              height: '100%',
              minHeight: '150px',
              background: '#0d1117',
              color: '#c9d1d9',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '8px',
              padding: '1rem',
              fontFamily: "'Cascadia Code', 'Fira Code', 'Consolas', monospace",
              fontSize: '14px',
              lineHeight: 1.6,
              resize: 'vertical',
              outline: 'none',
            }}
          />
        </div>

        {/* Terminal panel */}
        <div style={{
          flex: 1,
          minHeight: '200px',
          borderRadius: '8px',
          overflow: 'hidden',
        }}>
          <TerminalInner
            wsUrl={WS_URL}
            onStateChange={setTerminalState}
            onMount={ctrl => { terminalControl.current = ctrl }}
          />
        </div>
      </div>

      <footer style={{
        textAlign: 'center',
        fontSize: '0.8rem',
        color: '#4b5563',
        padding: '0.5rem',
      }}>
        SimplesEditor &copy; 2026 — Sprint 4: xterm.js integrado
      </footer>
    </div>
  )
}

/**
 * Componente interno que conecta o TerminalPanel e expoe o controle
 * para o componente pai via callback onMount.
 */
function TerminalInner({
  wsUrl,
  onStateChange,
  onMount,
}: {
  wsUrl: string
  onStateChange: (state: string) => void
  onMount: (ctrl: ReturnType<typeof useTerminal>) => void
}) {
  const ctrl = useTerminal({ wsUrl, onStateChange })

  useEffect(() => {
    onMount(ctrl)
  }, [ctrl, onMount])

  return (
    <TerminalPanel wsUrl={wsUrl} onStateChange={onStateChange} />
  )
}

export default App
