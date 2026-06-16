import { useState, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import type { Monaco } from '@monaco-editor/react'
import { SIMPLES_LANGUAGE_ID, simplesMonarchTokens } from './simplesLang'

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

function App() {
  const [code, setCode] = useState<string>(DEFAULT_CODE)
  const [healthStatus, setHealthStatus] = useState<string>('checking...')
  const [healthColor, setHealthColor] = useState<string>('#e2e8f0')
  // Sprint 2 — botao Run mockado
  const [runState, setRunState] = useState<'idle' | 'compiling' | 'done'>('idle')

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

  // Callback executado antes do Monaco montar
  const handleBeforeMount = (monaco: Monaco) => {
    registerSimplesLanguage(monaco)
  }

  // Sprint 2 — Run mockado: simula compilacao sem backend real
  const handleRun = () => {
    if (runState !== 'idle') return
    setRunState('compiling')
    setTimeout(() => {
      setRunState('done')
      setTimeout(() => setRunState('idle'), 1200)
    }, 2000)
  }

  // Icone Run (triangulo play)
  const IconRun = () => (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
      <path d="M4 2.5v11l9-5.5L4 2.5z" />
    </svg>
  )

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
            color: '#4b5563',
            fontSize: '0.85rem',
            fontFamily: "'JetBrains Mono', monospace",
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <p style={{ textAlign: 'center', lineHeight: 1.6 }}>
              O codigo assembly gerado aparecera aqui<br />
              <span style={{ fontSize: '0.75rem' }}>(Sprint 3 — Compilation Pipeline)</span>
            </p>
          </div>
        </aside>
      </main>

      {/* Footer with Run button */}
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
        <span>SIMPLES Editor v0.2.0 — Sprint 2</span>

        {/* Botao Run mockado (Sprint 2) */}
        <button
          onClick={handleRun}
          disabled={runState !== 'idle'}
          aria-label={runState === 'compiling' ? 'Compilando...' : runState === 'done' ? 'Concluido!' : 'Executar codigo'}
          title={runState === 'compiling' ? 'Compilando...' : runState === 'done' ? 'Compilacao concluida!' : 'Executar (mock)'}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 18px',
            border: 'none',
            borderRadius: '6px',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: runState === 'idle' ? 'pointer' : 'default',
            transition: 'all 0.2s ease',
            ...(runState === 'idle'
              ? {
                  backgroundColor: '#10b981',
                  color: '#ffffff',
                  boxShadow: '0 0 10px rgba(16, 185, 129, 0.25)',
                }
              : runState === 'compiling'
              ? {
                  backgroundColor: '#6366f1',
                  color: '#c7d2fe',
                  opacity: 0.85,
                }
              : {
                  backgroundColor: '#10b981',
                  color: '#ffffff',
                  boxShadow: '0 0 10px rgba(16, 185, 129, 0.35)',
                }),
          }}
        >
          {runState === 'compiling' ? (
            <>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none"
                style={{ animation: 'spin 1s linear infinite' }}>
                <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="2"
                  strokeDasharray="28" strokeDashoffset="8" />
              </svg>
              Compilando...
            </>
          ) : runState === 'done' ? (
            <>
              <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                <path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z" />
              </svg>
              Concluido!
            </>
          ) : (
            <>
              <IconRun />
              Run
            </>
          )}
        </button>

        <span>{code.split('\n').length} linhas</span>
      </footer>

      {/* Keyframes para animacao do spinner */}
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}

export default App
