import { useState, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import type { Monaco } from '@monaco-editor/react'
import { SIMPLES_LANGUAGE_ID, simplesMonarchTokens } from './simplesLang'
import { SIMPLES_DARK_THEME, defineSimplesTheme } from './simplesTheme'

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

// Registra linguagem SIMPLES e tema escuro no Monaco
function registerSimplesEditor(monaco: Monaco) {
  // Linguagem SIMPLES com tokenizer Monarch (27 palavras reservadas)
  monaco.languages.register({ id: SIMPLES_LANGUAGE_ID })
  monaco.languages.setMonarchTokensProvider(SIMPLES_LANGUAGE_ID, simplesMonarchTokens)

  // Tema escuro profissional (GitHub Dark + One Dark Pro adaptado)
  defineSimplesTheme(monaco)
  monaco.editor.setTheme(SIMPLES_DARK_THEME)
}

// Paleta de cores do tema escuro do SimplesEditor
const colors = {
  bg: '#0b0f19',
  surface: '#0d1117',
  surfaceRaised: 'rgba(17, 24, 39, 0.8)',
  border: 'rgba(255, 255, 255, 0.06)',
  borderSubtle: 'rgba(255, 255, 255, 0.04)',
  text: '#c9d1d9',
  textMuted: '#6b7280',
  textDim: '#4b5563',
  accent: '#6366f1',
  accentLight: '#a5b4fc',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  keyword: '#56b6c2',
  number: '#d19a66',
  string: '#e5c07b',
  comment: '#98c379',
  operator: '#c678dd',
}

function App() {
  const [code, setCode] = useState<string>(DEFAULT_CODE)
  const [healthStatus, setHealthStatus] = useState<string>('checking...')
  const [healthColor, setHealthColor] = useState<string>(colors.textMuted)
  const [, setMonacoInstance] = useState<Monaco | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setHealthStatus('ONLINE')
          setHealthColor(colors.success)
        } else {
          setHealthStatus('UNEXPECTED')
          setHealthColor(colors.warning)
        }
      })
      .catch(() => {
        setHealthStatus('OFFLINE')
        setHealthColor(colors.danger)
      })
  }, [])

  // Callback executado antes do Monaco montar — registra linguagem e tema
  const handleBeforeMount = (monaco: Monaco) => {
    registerSimplesEditor(monaco)
    setMonacoInstance(monaco)
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: colors.bg,
      color: colors.text,
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
        borderBottom: `1px solid ${colors.border}`,
        backgroundColor: colors.surfaceRaised,
        backdropFilter: 'blur(12px)',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <h1 style={{
            fontSize: '1rem',
            fontWeight: 700,
            margin: 0,
            background: `linear-gradient(135deg, ${colors.accentLight} 0%, ${colors.accent} 100%)`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            SIMPLES Editor
          </h1>
          {/* Keywords legend */}
          <div style={{ display: 'flex', gap: '8px', fontSize: '0.65rem' }}>
            <span style={{ color: colors.keyword }}>programa</span>
            <span style={{ color: colors.number }}>42</span>
            <span style={{ color: colors.string }}>"texto"</span>
            <span style={{ color: colors.comment }}>; comentario</span>
            <span style={{ color: colors.operator }}>&lt;-</span>
          </div>
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
          <span style={{ fontSize: '0.75rem', color: colors.textMuted, fontWeight: 500 }}>
            API: {healthStatus}
          </span>
        </div>
      </header>

      {/* Main layout: Editor + NASM panel */}
      <main style={{
        flex: 1,
        display: 'flex',
        overflow: 'hidden',
      }}>
        {/* Code Editor (SIMPLES) */}
        <section style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          borderRight: `1px solid ${colors.border}`,
        }}>
          {/* Tab bar */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            padding: '0.35rem 1rem',
            borderBottom: `1px solid ${colors.borderSubtle}`,
            backgroundColor: colors.surfaceRaised,
            gap: '12px',
          }}>
            <span style={{
              fontSize: '0.7rem',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              color: colors.accentLight,
              fontWeight: 600,
            }}>
              Editor (SIMPLES)
            </span>
            <span style={{
              fontSize: '0.65rem',
              color: colors.textDim,
            }}>
              27 keywords • syntax highlighting • tema dark
            </span>
          </div>
          {/* Monaco Editor */}
          <div style={{ flex: 1 }}>
            <Editor
              height="100%"
              language={SIMPLES_LANGUAGE_ID}
              value={code}
              onChange={value => setCode(value ?? '')}
              theme={SIMPLES_DARK_THEME}
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
                bracketPairColorization: { enabled: true },
                guides: { indentation: true, bracketPairs: true },
                smoothScrolling: true,
                cursorBlinking: 'smooth',
                cursorSmoothCaretAnimation: 'on',
                padding: { top: 8 },
              }}
            />
          </div>
        </section>

        {/* NASM Output panel (read-only — Sprint 2 placeholder, Sprint 3 funcional) */}
        <aside style={{
          width: '40%',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: colors.surface,
        }}>
          <div style={{
            padding: '0.35rem 1rem',
            fontSize: '0.7rem',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            color: colors.textMuted,
            borderBottom: `1px solid ${colors.borderSubtle}`,
            backgroundColor: colors.surfaceRaised,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            NASM Output
            <span style={{
              fontSize: '0.6rem',
              padding: '1px 6px',
              borderRadius: '3px',
              background: 'rgba(255, 255, 255, 0.05)',
              color: colors.textDim,
            }}>
              read-only
            </span>
          </div>
          <div style={{
            flex: 1,
            padding: '1.5rem',
            color: colors.textDim,
            fontSize: '0.85rem',
            fontFamily: "'JetBrains Mono', monospace",
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
          }}>
            <span style={{ fontSize: '2rem', opacity: 0.3 }}>⚙</span>
            <p style={{ textAlign: 'center', lineHeight: 1.6, margin: 0 }}>
              Assembly x86 gerado aparecera aqui
            </p>
            <span style={{ fontSize: '0.7rem', color: colors.textDim }}>
              Sprint 3 — Compilation Pipeline
            </span>
          </div>
        </aside>
      </main>

      {/* Footer */}
      <footer style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.35rem 1rem',
        borderTop: `1px solid ${colors.border}`,
        backgroundColor: colors.surfaceRaised,
        fontSize: '0.7rem',
        color: colors.textDim,
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', gap: '12px' }}>
          <span>SIMPLES Editor v0.2.0</span>
          <span style={{ color: colors.border }}>|</span>
          <span>Sprint 2 — Editor &amp; NASM Panel</span>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ color: colors.keyword }}>●</span> keywords
          <span style={{ color: colors.number }}>●</span> numeros
          <span style={{ color: colors.comment }}>●</span> comentarios
          <span style={{ color: colors.textDim, marginLeft: '8px' }}>
            {code.split('\n').length} linhas
          </span>
        </div>
      </footer>
    </div>
  )
}

export default App
