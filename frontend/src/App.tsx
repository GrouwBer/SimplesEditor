import { useState, useEffect, useRef } from 'react'
import Editor from '@monaco-editor/react'
import type { Monaco } from '@monaco-editor/react'
import type { editor } from 'monaco-editor'
import { SIMPLES_LANGUAGE_ID, simplesMonarchTokens } from './simplesLang'
import { SIMPLES_DARK_THEME, defineSimplesTheme } from './simplesTheme'
import { SplitPane } from './components/SplitPane'

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

const DEFAULT_NASM = [
  '; NASM gerado pelo simplesc',
  '; O assembly aparecera aqui apos a compilacao',
  '',
  'section .data',
  'section .bss',
  'section .text',
  '    global _start',
  '_start:',
  '    mov eax, 1',
  '    xor ebx, ebx',
  '    int 0x80',
].join('\n')

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
}

interface CompileError {
  line: number
  column: number
  message: string
  phase: string
}

interface CompileResponse {
  success: boolean
  asm?: string
  errors?: CompileError[]
  error?: string
}

function registerSimplesEditor(monaco: Monaco) {
  monaco.languages.register({ id: SIMPLES_LANGUAGE_ID })
  monaco.languages.setMonarchTokensProvider(SIMPLES_LANGUAGE_ID, simplesMonarchTokens)
  defineSimplesTheme(monaco)
}

function App() {
  const [code, setCode] = useState<string>(DEFAULT_CODE)
  const [nasmCode, setNasmCode] = useState<string>(DEFAULT_NASM)
  const [healthStatus, setHealthStatus] = useState<string>('checking...')
  const [healthColor, setHealthColor] = useState<string>(colors.textMuted)
  const [compileStatus, setCompileStatus] = useState<string>('')
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null)

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

  const handleBeforeMount = (monaco: Monaco) => {
    registerSimplesEditor(monaco)
  }

  const handleEditorMount = (editor: editor.IStandaloneCodeEditor) => {
    editorRef.current = editor
  }

  // Limpa markers de erro anteriores
  const clearErrorMarkers = () => {
    if (!editorRef.current) return
    const model = editorRef.current.getModel()
    if (!model) return
    import('monaco-editor').then(m => {
      m.editor.setModelMarkers(model, 'simples-compile', [])
    })
  }

  // Exibe erros como markers no Monaco
  const showErrorMarkers = (errors: CompileError[]) => {
    if (!editorRef.current) return
    const model = editorRef.current.getModel()
    if (!model) return

    import('monaco-editor').then(m => {
      const markers: editor.IMarkerData[] = errors.map(err => ({
        severity: m.MarkerSeverity.Error,
        message: `[${err.phase}] ${err.message}`,
        startLineNumber: err.line,
        startColumn: err.column,
        endLineNumber: err.line,
        endColumn: err.column + 10,
      }))
      m.editor.setModelMarkers(model, 'simples-compile', markers)
    })
  }

  // Compila codigo via REST API
  const handleCompile = async () => {
    setCompileStatus('Compilando...')
    clearErrorMarkers()

    try {
      const res = await fetch('/api/compile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
      const data: CompileResponse = await res.json()

      if (data.success && data.asm) {
        setNasmCode(data.asm)
        setCompileStatus('Compilacao OK')
        setTimeout(() => setCompileStatus(''), 3000)
      } else if (data.errors && data.errors.length > 0) {
        showErrorMarkers(data.errors)
        setCompileStatus(`${data.errors.length} erro(s) encontrado(s)`)
      } else {
        setCompileStatus(`Erro: ${data.error ?? 'desconhecido'}`)
      }
    } catch {
      setCompileStatus('Erro de conexao com backend')
    }
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
          {/* Botao Compilar */}
          <button
            onClick={handleCompile}
            style={{
              padding: '0.3rem 1rem',
              background: `linear-gradient(135deg, ${colors.accent} 0%, #4f46e5 100%)`,
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              fontWeight: 600,
              cursor: 'pointer',
              fontSize: '0.75rem',
            }}
          >
            Compilar
          </button>
          {compileStatus && (
            <span style={{
              fontSize: '0.7rem',
              color: compileStatus.includes('erro') || compileStatus.includes('Erro')
                ? colors.danger
                : compileStatus === 'Compilacao OK'
                  ? colors.success
                  : colors.warning,
            }}>
              {compileStatus}
            </span>
          )}
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

      {/* Main layout com splitter */}
      <main style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <SplitPane defaultLeftWidth={60} minLeftWidth={30} minRightWidth={20}>
          {/* === Editor SIMPLES === */}
          <section style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
          }}>
            <div style={{
              padding: '0.3rem 1rem',
              fontSize: '0.7rem',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              color: colors.accentLight,
              fontWeight: 600,
              borderBottom: `1px solid ${colors.borderSubtle}`,
              backgroundColor: colors.surfaceRaised,
            }}>
              Editor (SIMPLES)
            </div>
            <div style={{ flex: 1 }}>
              <Editor
                height="100%"
                language={SIMPLES_LANGUAGE_ID}
                value={code}
                onChange={value => setCode(value ?? '')}
                theme={SIMPLES_DARK_THEME}
                beforeMount={handleBeforeMount}
                onMount={handleEditorMount}
                options={{
                  fontSize: 14,
                  fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
                  minimap: { enabled: false },
                  lineNumbers: 'on',
                  renderWhitespace: 'selection',
                  tabSize: 4,
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  bracketPairColorization: { enabled: true },
                  padding: { top: 8 },
                }}
              />
            </div>
          </section>

          {/* === NASM read-only === */}
          <aside style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            backgroundColor: colors.surface,
          }}>
            <div style={{
              padding: '0.3rem 1rem',
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
                background: 'rgba(239, 68, 68, 0.15)',
                color: colors.danger,
              }}>
                read-only
              </span>
            </div>
            <div style={{ flex: 1 }}>
              <Editor
                height="100%"
                language="asm"
                value={nasmCode}
                theme={SIMPLES_DARK_THEME}
                beforeMount={handleBeforeMount}
                options={{
                  readOnly: true,
                  domReadOnly: true,
                  fontSize: 13,
                  fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
                  minimap: { enabled: false },
                  lineNumbers: 'on',
                  renderWhitespace: 'none',
                  tabSize: 4,
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  padding: { top: 8 },
                  overviewRulerLanes: 0,
                  hideCursorInOverviewRuler: true,
                  renderLineHighlight: 'none',
                  glyphMargin: false,
                  folding: true,
                  lineDecorationsWidth: 0,
                  lineNumbersMinChars: 3,
                }}
              />
            </div>
          </aside>
        </SplitPane>
      </main>

      {/* Footer */}
      <footer style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.3rem 1rem',
        borderTop: `1px solid ${colors.border}`,
        backgroundColor: colors.surfaceRaised,
        fontSize: '0.7rem',
        color: colors.textDim,
        flexShrink: 0,
      }}>
        <span>SIMPLES Editor v0.3.0 — Sprint 3: Compilation Pipeline</span>
        <div style={{ display: 'flex', gap: '16px' }}>
          <span>SIMPLES: {code.split('\n').length} linhas</span>
          <span>NASM: {nasmCode.split('\n').length} linhas</span>
        </div>
      </footer>
    </div>
  )
}

export default App
