import { useState, useEffect } from 'react'
import Editor, { type BeforeMount } from '@monaco-editor/react'
import { Group, Panel, Separator } from 'react-resizable-panels'
import { SIMPLES_LANGUAGE_ID, simplesMonarchTokens } from './simplesLang'
import { SIMPLES_DARK_THEME, defineSimplesTheme } from './simplesTheme'

// Exemplo de codigo SIMPLES (didatico, em portugues estruturado)
const DEFAULT_CODE = `programa Exemplo
  inteiro x, y

inicio
  leia(x)
  leia(y)

  se x > y entao
    escreval("x e maior que y")
  senao
    escreval("y e maior ou igual a x")
  fimse

  para i de 1 ate 10 passo 1 faca
    escreval(i)
  fimpara
fim
`

const DEFAULT_NASM = `; Assembly gerado aparecera aqui apos compilacao
; (Sprint 3 — Compilation Pipeline)`

function App() {
  const [code, setCode] = useState<string>(DEFAULT_CODE)
  const [healthStatus, setHealthStatus] = useState<string>('checking...')
  const [healthColor, setHealthColor] = useState<string>('#e2e8f0')
  const [nasmCollapsed, setNasmCollapsed] = useState(false)

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

  // Registra a linguagem SIMPLES e o tema antes do editor montar
  const handleBeforeMount: BeforeMount = (monaco) => {
    monaco.languages.register({ id: SIMPLES_LANGUAGE_ID })
    monaco.languages.setMonarchTokensProvider(SIMPLES_LANGUAGE_ID, simplesMonarchTokens)
    defineSimplesTheme(monaco)
  }

  const editorOptions = {
    fontSize: 14,
    fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
    minimap: { enabled: true as const },
    lineNumbers: 'on' as const,
    renderWhitespace: 'selection' as const,
    tabSize: 2,
    wordWrap: 'off' as const,
    scrollBeyondLastLine: false,
    automaticLayout: true,
  }

  const nasmOptions = {
    readOnly: true,
    fontSize: 13,
    fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
    minimap: { enabled: false as const },
    lineNumbers: 'on' as const,
    renderWhitespace: 'selection' as const,
    tabSize: 2,
    wordWrap: 'off' as const,
    scrollBeyondLastLine: false,
    automaticLayout: true,
  }

  return (
    <div style={{
      height: '100vh',
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
        minHeight: '40px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
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
          <button
            onClick={() => setNasmCollapsed(prev => !prev)}
            title={nasmCollapsed ? 'Mostrar painel NASM' : 'Ocultar painel NASM'}
            style={{
              fontSize: '0.7rem',
              padding: '0.2rem 0.6rem',
              borderRadius: '4px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              background: nasmCollapsed
                ? 'rgba(86, 182, 194, 0.1)'
                : 'rgba(255, 255, 255, 0.05)',
              color: nasmCollapsed ? '#56b6c2' : '#8b949e',
              cursor: 'pointer',
            }}
          >
            {nasmCollapsed ? '\u25B8 NASM' : '\u25BE NASM'}
          </button>
        </div>
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

      {/* Main area */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Upper: Editor + NASM (horizontal split) */}
        <Group orientation="horizontal" style={{ flex: 1, overflow: 'hidden' }}>
          {/* Left: SIMPLES Code Editor */}
          <Panel defaultSize={nasmCollapsed ? 100 : 60} minSize={30}>
            <section style={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
            }}>
              <div style={{
                padding: '0.35rem 1rem',
                fontSize: '0.7rem',
                textTransform: 'uppercase',
                letterSpacing: '0.1em',
                color: '#6b7280',
                borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                backgroundColor: 'rgba(17, 24, 39, 0.6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexShrink: 0,
              }}>
                <span>Editor (SIMPLES)</span>
                <span style={{
                  fontSize: '0.6rem',
                  color: '#56b6c2',
                  background: 'rgba(86, 182, 194, 0.1)',
                  padding: '0.1rem 0.4rem',
                  borderRadius: '3px',
                }}>
                  27 keywords
                </span>
              </div>
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <Editor
                  height="100%"
                  language={SIMPLES_LANGUAGE_ID}
                  value={code}
                  onChange={(value) => setCode(value || '')}
                  theme={SIMPLES_DARK_THEME}
                  beforeMount={handleBeforeMount}
                  options={editorOptions}
                />
              </div>
            </section>
          </Panel>

          {/* Resizable splitter (only when NASM is visible) */}
          {!nasmCollapsed && (
            <Separator
              style={{
                width: '6px',
                background: 'rgba(255, 255, 255, 0.04)',
              }}
            />
          )}

          {/* Right: NASM Output Panel (collapsible) */}
          {!nasmCollapsed && (
            <Panel defaultSize={40} minSize={20}>
              <aside style={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
              }}>
                <div style={{
                  padding: '0.35rem 1rem',
                  fontSize: '0.7rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                  color: '#6b7280',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                  backgroundColor: 'rgba(17, 24, 39, 0.6)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexShrink: 0,
                }}>
                  <span>NASM Output (read-only)</span>
                  <button
                    onClick={() => setNasmCollapsed(true)}
                    title="Fechar painel NASM"
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#6b7280',
                      cursor: 'pointer',
                      fontSize: '0.8rem',
                      padding: '0 0.2rem',
                    }}
                  >
                    {'\u2715'}
                  </button>
                </div>
                <div style={{ flex: 1, overflow: 'hidden' }}>
                  <Editor
                    height="100%"
                    defaultLanguage="asm"
                    value={DEFAULT_NASM}
                    theme={SIMPLES_DARK_THEME}
                    beforeMount={handleBeforeMount}
                    options={nasmOptions}
                  />
                </div>
              </aside>
            </Panel>
          )}
        </Group>

        {/* Bottom: Terminal panel (placeholder) */}
        <div style={{
          height: '25%',
          minHeight: '60px',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: 'rgba(13, 17, 23, 0.95)',
        }}>
          <div style={{
            padding: '0.35rem 1rem',
            fontSize: '0.7rem',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            color: '#6b7280',
            borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
            backgroundColor: 'rgba(17, 24, 39, 0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexShrink: 0,
          }}>
            <span>Terminal</span>
            <span style={{ fontSize: '0.6rem', color: '#4b5563' }}>
              (Sprint 3 — xterm.js + WebSocket)
            </span>
          </div>
          <div style={{
            flex: 1,
            padding: '0.75rem 1rem',
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            fontSize: '0.8rem',
            color: '#4b5563',
            overflowY: 'auto',
            whiteSpace: 'pre-wrap',
          }}>
            <span style={{ color: '#56b6c2' }}>$ </span>
            <span style={{ opacity: 0.5 }}> Terminal interativo disponivel na Sprint 3</span>
            {'\n'}
            <span style={{ color: '#56b6c2' }}>$ </span>
            <span style={{ opacity: 0.3 }}>{'\u25CA'}</span>
          </div>
        </div>
      </main>

      {/* Bottom status bar */}
      <footer style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.3rem 1rem',
        borderTop: '1px solid rgba(255, 255, 255, 0.06)',
        backgroundColor: 'rgba(17, 24, 39, 0.8)',
        fontSize: '0.7rem',
        color: '#4b5563',
        flexShrink: 0,
        minHeight: '24px',
      }}>
        <span>SIMPLES Editor v0.2.0</span>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <span>{code.split('\n').length} linhas</span>
          {!nasmCollapsed && <span>NASM visivel</span>}
        </div>
      </footer>
    </div>
  )
}

export default App
