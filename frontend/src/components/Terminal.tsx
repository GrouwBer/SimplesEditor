import { useState, useRef, useEffect, type FC, type KeyboardEvent } from 'react'
import type { TerminalLine } from '../hooks/useTerminal'
import type { ExecutionState } from '../hooks/useExecution'

interface TerminalProps {
  /** Linhas de output + stdin do buffer */
  lines: TerminalLine[]
  /** Estado atual da execucao */
  execState: ExecutionState
  /** Exit code da ultima execucao */
  exitCode: number | null
  /** Duracao da ultima execucao em ms */
  durationMs: number | null
  /** Callback para enviar stdin ao backend */
  onSendStdin: (data: string) => boolean
  /** Callback para limpar o terminal */
  onClear: () => void
}

/**
 * Terminal interativo que suporta o fluxo `leia` (stdin).
 *
 * RF11: stdout transmitido em tempo real — renderiza cada linha recebida.
 * RF12: Input do usuario vai para stdin do binario — campo de texto
 *       que envia {type: "stdin", data: "..."} ao pressionar Enter.
 */
const Terminal: FC<TerminalProps> = ({
  lines,
  execState,
  exitCode,
  durationMs,
  onSendStdin,
  onClear,
}) => {
  const [inputValue, setInputValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll para o final quando novas linhas chegam
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [lines])

  // Foca o input quando entramos no estado executing
  useEffect(() => {
    if (execState === 'executing' && inputRef.current) {
      inputRef.current.focus()
    }
  }, [execState])

  // Envia stdin ao pressionar Enter (RF12)
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault()
      const sent = onSendStdin(inputValue.trim())
      if (sent) {
        setInputValue('')
      }
    }
  }

  // O terminal aceita input apenas durante execucao (executing)
  const isInteractive = execState === 'executing'

  return (
    <div style={styles.container}>
      {/* Cabecalho do terminal */}
      <div style={styles.header}>
        <span style={styles.headerTitle}>Terminal</span>
        <div style={styles.headerRight}>
          {execState === 'executing' && (
            <span style={styles.statusExecuting}>executando...</span>
          )}
          {exitCode !== null && (
            <span style={{
              ...styles.exitCode,
              color: exitCode === 0 ? '#10b981' : '#ef4444',
            }}>
              exit: {exitCode}
              {durationMs !== null ? ` (${(durationMs / 1000).toFixed(2)}s)` : ''}
            </span>
          )}
          <button
            onClick={onClear}
            style={styles.clearButton}
            title="Limpar terminal"
          >
            limpar
          </button>
        </div>
      </div>

      {/* Area de output do terminal */}
      <div ref={scrollRef} style={styles.output}>
        {lines.length === 0 && execState === 'idle' && (
          <div style={styles.emptyState}>
            <span style={styles.prompt}>$</span>
            <span style={styles.emptyText}>
              Aguardando execucao... Clique Run para compilar e executar.
            </span>
          </div>
        )}

        {lines.map((line) => (
          <div
            key={line.id}
            style={{
              ...styles.line,
              color: line.type === 'stderr' ? '#ef4444'
                     : line.type === 'stdin' ? '#f59e0b'
                     : '#e5e7eb',
            }}
          >
            {line.type === 'stdin' ? (
              <>
                <span style={styles.prompt}>$</span>
                <span>{line.text}</span>
              </>
            ) : (
              <span style={{ whiteSpace: 'pre-wrap' }}>{line.text}</span>
            )}
          </div>
        ))}

        {/* Prompt de input interativo (RF12) */}
        {isInteractive && (
          <div style={styles.inputLine}>
            <span style={styles.prompt}>$</span>
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite aqui e pressione Enter..."
              autoFocus
              style={styles.input}
            />
          </div>
        )}

        {/* Indicador de estado quando nao e interativo */}
        {execState === 'compiling' && (
          <div style={styles.stateIndicator}>
            <span style={{ color: '#6366f1' }}>Compilando...</span>
          </div>
        )}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    background: 'rgba(0, 0, 0, 0.35)',
    borderTop: '1px solid rgba(255, 255, 255, 0.06)',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0.4rem 1rem',
    background: 'rgba(255, 255, 255, 0.02)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
  },
  headerTitle: {
    fontSize: '0.8rem',
    fontWeight: 600,
    color: '#9ca3af',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  statusExecuting: {
    fontSize: '0.7rem',
    color: '#f59e0b',
    fontWeight: 500,
  },
  exitCode: {
    fontSize: '0.7rem',
    fontWeight: 600,
  },
  clearButton: {
    background: 'none',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    color: '#6b7280',
    fontSize: '0.7rem',
    padding: '2px 8px',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  output: {
    flex: 1,
    overflowY: 'auto',
    padding: '0.5rem 1rem',
    fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
    fontSize: '0.85rem',
    lineHeight: 1.5,
  },
  emptyState: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '0.25rem 0',
  },
  emptyText: {
    color: '#4b5563',
    fontSize: '0.8rem',
  },
  prompt: {
    color: '#10b981',
    fontWeight: 700,
    marginRight: '8px',
    userSelect: 'none',
  },
  line: {
    padding: '0.1rem 0',
    fontSize: '0.85rem',
    fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
  },
  inputLine: {
    display: 'flex',
    alignItems: 'center',
    padding: '0.25rem 0',
  },
  input: {
    flex: 1,
    background: 'transparent',
    border: 'none',
    outline: 'none',
    color: '#f3f4f6',
    fontSize: '0.85rem',
    fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
    caretColor: '#10b981',
  },
  stateIndicator: {
    padding: '0.5rem 0',
    textAlign: 'center',
    fontSize: '0.8rem',
  },
}

export default Terminal
