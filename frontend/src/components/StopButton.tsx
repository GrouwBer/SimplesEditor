import { type FC } from 'react'
import type { ExecutionState } from '../hooks/useExecution'

interface StopButtonProps {
  /** Estado atual da execucao */
  state: ExecutionState
  /** Callback para enviar comando Stop via WebSocket */
  onStop: () => void
}

// ICONES SVG inline (sem dependencia externa)

const IconStop = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
    <rect x="3" y="3" width="10" height="10" rx="1" />
  </svg>
)

const IconSpinner = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none"
    style={{ animation: 'spin 1s linear infinite' }}>
    <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="2"
      strokeDasharray="28" strokeDashoffset="8" />
    <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
  </svg>
)

/**
 * Botao Stop funcional (RF13)
 *
 * Comportamento:
 * - Estado idle: exibe borao Run (verde) → inicia execucao
 * - Estado compiling: exibe spinner + texto "Compilando..." (desabilitado)
 * - Estado executing: exibe borao Stop (vermelho) → envia {type: "stop"}
 * - Estado finished: exibe borao Run (verde) → pronto para nova execucao
 *
 * RF13: Ao clicar Stop, envia SIGTERM ao processo (backend),
 *       depois SIGKILL apos 1s. Tempo total ≤ 2s.
 *
 * PRD secao 12.2: "Ao clicar Stop: envia {type: 'stop'} ao servidor;
 * UI volta a estado idle ao receber exit."
 */
const StopButton: FC<StopButtonProps> = ({ state, onStop }) => {
  if (state === 'compiling') {
    return (
      <button
        disabled
        aria-label="Compilando"
        style={styles.buttonCompiling}
      >
        <IconSpinner />
        <span>Compilando...</span>
      </button>
    )
  }

  if (state === 'executing') {
    return (
      <button
        onClick={onStop}
        aria-label="Parar execucao"
        title="Interromper execucao (SIGTERM → SIGKILL)"
        style={styles.buttonStop}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = '#dc2626' // red-600
          e.currentTarget.style.transform = 'scale(1.05)'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = '#ef4444' // red-500
          e.currentTarget.style.transform = 'scale(1)'
        }}
      >
        <IconStop />
        <span>Stop</span>
      </button>
    )
  }

  // idle ou finished — o botao Run (verde) e renderizado pelo componente Toolbar
  return null
}

const styles: Record<string, React.CSSProperties> = {
  buttonStop: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 20px',
    backgroundColor: '#ef4444', // red-500
    color: '#ffffff',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.95rem',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.15s ease',
    boxShadow: '0 0 12px rgba(239, 68, 68, 0.3)',
  },
  buttonCompiling: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 20px',
    backgroundColor: '#6366f1', // indigo-500
    color: '#c7d2fe',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.95rem',
    fontWeight: 600,
    cursor: 'not-allowed',
    opacity: 0.8,
  },
}

export default StopButton
