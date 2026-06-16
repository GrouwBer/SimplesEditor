import { useState, useEffect, useRef, useCallback } from 'react'

interface SplitPaneProps {
  defaultLeftWidth: number // percentage 0-100
  minLeftWidth: number
  minRightWidth: number
  children: [React.ReactNode, React.ReactNode]
}

/**
 * SplitPane redimensionavel com handle arrastavel.
 * Usa CSS + eventos de mouse para redimensionamento fluido.
 */
export function SplitPane({
  defaultLeftWidth,
  minLeftWidth,
  minRightWidth,
  children,
}: SplitPaneProps) {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth)
  const [isDragging, setIsDragging] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  useEffect(() => {
    if (!isDragging) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const newLeftPercent = ((e.clientX - rect.left) / rect.width) * 100
      const clamped = Math.max(minLeftWidth, Math.min(100 - minRightWidth, newLeftPercent))
      setLeftWidth(clamped)
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    // Previne selecao de texto durante o drag
    document.body.style.userSelect = 'none'
    document.body.style.cursor = 'col-resize'

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
    }
  }, [isDragging, minLeftWidth, minRightWidth])

  return (
    <div ref={containerRef} style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
      {/* Painel esquerdo */}
      <div style={{ width: `${leftWidth}%`, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {children[0]}
      </div>

      {/* Handle arrastavel */}
      <div
        onMouseDown={handleMouseDown}
        style={{
          width: '5px',
          cursor: 'col-resize',
          backgroundColor: isDragging
            ? 'rgba(99, 102, 241, 0.6)'
            : 'rgba(255, 255, 255, 0.06)',
          transition: isDragging ? 'none' : 'background-color 0.2s',
          flexShrink: 0,
          position: 'relative',
          zIndex: 10,
        }}
        onMouseEnter={e => {
          if (!isDragging) {
            (e.target as HTMLElement).style.backgroundColor = 'rgba(99, 102, 241, 0.3)'
          }
        }}
        onMouseLeave={e => {
          if (!isDragging) {
            (e.target as HTMLElement).style.backgroundColor = 'rgba(255, 255, 255, 0.06)'
          }
        }}
      >
        {/* Indicador visual central */}
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '3px',
          height: '32px',
          borderRadius: '2px',
          backgroundColor: isDragging ? 'rgba(99, 102, 241, 0.8)' : 'rgba(255, 255, 255, 0.1)',
          transition: isDragging ? 'none' : 'background-color 0.2s',
        }} />
      </div>

      {/* Painel direito */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {children[1]}
      </div>
    </div>
  )
}
