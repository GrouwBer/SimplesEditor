import { useTerminal, TerminalState } from '../hooks/useTerminal'

interface TerminalProps {
  wsUrl: string
  onStateChange?: (state: TerminalState) => void
  className?: string
}

/**
 * Componente de terminal interativo usando xterm.js.
 * Conecta via WebSocket ao backend para execucao de codigo SIMPLES.
 *
 * Expor as funcoes de controle via ref seria ideal, mas para manter
 * compatibilidade com o fluxo atual da Sprint 4, o controle e feito
 * pelo componente pai atraves de comunicacao entre hooks.
 */
export function TerminalPanel({ wsUrl, onStateChange, className }: TerminalProps) {
  const { terminalRef } = useTerminal({
    wsUrl,
    onStateChange,
  })

  return (
    <div
      ref={terminalRef}
      className={className}
      style={{
        width: '100%',
        height: '100%',
        minHeight: '200px',
        borderRadius: '8px',
        overflow: 'hidden',
        border: '1px solid rgba(255, 255, 255, 0.08)',
      }}
    />
  )
}

// Re-exporta o hook para uso externo
export { useTerminal }
export type { TerminalState }
