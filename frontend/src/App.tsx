import { useState, useEffect, useRef } from 'react'
import Editor from '@monaco-editor/react'
import type { Monaco } from '@monaco-editor/react'
import { SIMPLES_LANGUAGE_ID, simplesMonarchTokens } from './simplesLang'
import { AuthProvider, useAuth } from './AuthContext'
import LoginPage from './pages/LoginPage'
import { useExecution } from './hooks/useExecution'
import { useTerminal } from './hooks/useTerminal'
import Terminal from './components/Terminal'

const DEFAULT_CODE = [
  'programa exemplo_soma',
  '  inteiro a, b, resultado',
  'inicio',
  '  leia a',
  '  leia b',
  '  resultado <- a + b',
  '  escreval resultado',
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

  // WebSocket connection
  const wsRef = useRef<WebSocket | null>(null)
  const { state, exitCode, durationMs, sendRun, sendStop, handleMessage } = useExecution(wsRef)
  const { lines, appendOutput, sendStdin, clearTerminal } = useTerminal(wsRef)

  useEffect(() => {
    // Conecta WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/run`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('[App] WebSocket conectado')
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        handleMessage(msg)
        // Atualiza NASM output quando disponivel
        if (msg.asm) {
          setNasmOutput(msg.asm)
        }
        // Adiciona stdout/stderr ao terminal
        if (msg.type === 'stdout' || msg.type === 'stderr') {
          appendOutput(msg.data || '', msg.type as 'stdout' | 'stderr')
        }
      } catch (e) {
        console.error('[App] Erro ao processar mensagem WS:', e)
      }
    }

    ws.onclose = () => {
      console.log('[App] WebSocket desconectado')
    }

    wsRef.current = ws

    return () => {
      try {
        ws.close()
      } catch (e) {
        console.error('[App] Erro ao fechar WebSocket:', e)
      }
      wsRef.current = null
    }
  }, [handleMessage])

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
              onClick={() => sendRun(code)}
              style={{
                padding: '4px 12px',
                fontSize: '0.75rem',
                fontWeight: 600,
                borderRadius: '4px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: state === 'finished' ? '#059669' : '#6366f1',
                color: '#fff',
              }}
            >
              {state === 'finished' ? 'EXECUTAR NOVAMENTE' : 'EXECUTAR'}
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
        </div>
      </header>

      {/* Main layout */}
      <main style={{
        flex: 1,
        display: 'flex',
        overflow: 'hidden',
      }}>
        {/* Code Editor */}
        <section style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          borderRight: '1px solid rgba(255, 255, 255, 0.06)',
        }}>
          <div style={{
            padding: '0.35rem 1rem',
            fontSize: '0.7rem',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            color: '#6b7280',
            borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
            backgroundColor: 'rgba(17, 24, 39, 0.6)',
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
          width: '40%',
          display: 'flex',
          flexDirection: 'column',
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
          }}>
            NASM Output (read-only)
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
      </main>

      {/* Terminal */}
      <div style={{
        height: '200px',
        flexShrink: 0,
      }}>
        <Terminal
          lines={lines}
          execState={state}
          exitCode={exitCode}
          durationMs={durationMs}
          onSendStdin={sendStdin}
          onClear={clearTerminal}
        />
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
