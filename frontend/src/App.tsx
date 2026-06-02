import { useState, useEffect } from 'react'
import Editor from '@monaco-editor/react'

const DEFAULT_CODE = `; SIMPLES - Exemplo
section .data
    msg db 'Hello, SIMPLES!', 0

section .text
    global _start

_start:
    ; Seu codigo aqui
    mov eax, 1
    mov ebx, 0
    int 0x80
`

function App() {
  const [code, setCode] = useState<string>(DEFAULT_CODE)
  const [healthStatus, setHealthStatus] = useState<string>('checking...')
  const [healthColor, setHealthColor] = useState<string>('#e2e8f0')

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
      {/* Top bar */}
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

      {/* Editor area */}
      <main style={{
        flex: 1,
        display: 'flex',
        overflow: 'hidden',
      }}>
        {/* Code Editor Panel */}
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
              defaultLanguage="asm"
              value={code}
              onChange={(value) => setCode(value || '')}
              theme="vs-dark"
              options={{
                fontSize: 14,
                fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
                minimap: { enabled: true },
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

        {/* Right panel placeholder (NASM output - Sprint 2 / issue #14) */}
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
              ⏳ O codigo assembly gerado aparecera aqui<br />
              <span style={{ fontSize: '0.75rem' }}>(Sprint 3 — Compilation Pipeline)</span>
            </p>
          </div>
        </aside>
      </main>

      {/* Bottom bar */}
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
        <span>SIMPLES Editor v0.1.0</span>
        <span>{code.split('\n').length} linhas</span>
      </footer>
    </div>
  )
}

export default App
