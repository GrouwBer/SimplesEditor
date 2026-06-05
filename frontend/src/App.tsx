import { useState, useEffect } from 'react'

function App() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...')
  const [healthColor, setHealthColor] = useState<string>('#e2e8f0')

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          setHealthStatus('ONLINE')
          setHealthColor('#10b981') // emerald-500
        } else {
          setHealthStatus('UNEXPECTED RESPONSE')
          setHealthColor('#f59e0b') // amber-500
        }
      })
      .catch(() => {
        setHealthStatus('OFFLINE')
        setHealthColor('#ef4444') // red-500
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
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Decorative background glows */}
      <div style={{
        position: 'absolute',
        width: '300px',
        height: '300px',
        background: 'radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, rgba(0,0,0,0) 70%)',
        top: '10%',
        left: '20%',
        zIndex: 0,
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute',
        width: '350px',
        height: '350px',
        background: 'radial-gradient(circle, rgba(236, 72, 153, 0.1) 0%, rgba(0,0,0,0) 70%)',
        bottom: '15%',
        right: '15%',
        zIndex: 0,
        pointerEvents: 'none',
      }} />

      <main style={{
        position: 'relative',
        zIndex: 1,
        maxWidth: '600px',
        width: '100%',
        background: 'rgba(17, 24, 39, 0.7)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '16px',
        padding: '2.5rem',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4)',
        textAlign: 'center',
      }}>
        {/* Logo/Header */}
        <h1 style={{
          fontSize: '2.5rem',
          fontWeight: 800,
          margin: '0 0 0.5rem 0',
          background: 'linear-gradient(135deg, #a5b4fc 0%, #6366f1 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '-0.025em',
        }}>
          SIMPLES
        </h1>
        <p style={{
          color: '#9ca3af',
          fontSize: '1rem',
          marginBottom: '2rem',
          fontWeight: 400,
        }}>
          Editor de código e pipeline de execução interativa
        </p>

        {/* Sprint Status Panel */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          borderRadius: '12px',
          padding: '1.5rem',
          marginBottom: '2rem',
          textAlign: 'left',
        }}>
          <h3 style={{
            margin: '0 0 1rem 0',
            fontSize: '1.1rem',
            color: '#e5e7eb',
            fontWeight: 600,
          }}>
            Sprint 1: Foundation & DevOps
          </h3>
          <ul style={{
            margin: 0,
            paddingLeft: '1.25rem',
            color: '#9ca3af',
            lineHeight: 1.6,
          }}>
            <li>docker-compose local stack validado</li>
            <li>Nginx reverse proxy funcionando</li>
            <li>Skeleton React + Flask integrado</li>
          </ul>
        </div>

        {/* Backend Connectivity Status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(255, 255, 255, 0.02)',
          padding: '1rem 1.5rem',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.03)',
        }}>
          <span style={{ fontSize: '0.95rem', color: '#9ca3af', fontWeight: 500 }}>
            Status da API do Backend:
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              display: 'inline-block',
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: healthColor,
              boxShadow: `0 0 8px ${healthColor}`,
              transition: 'all 0.3s ease',
            }} />
            <span style={{
              fontSize: '0.95rem',
              fontWeight: 700,
              color: healthColor,
              letterSpacing: '0.05em',
            }}>
              {healthStatus}
            </span>
          </div>
        </div>
      </main>

      <footer style={{
        marginTop: '2rem',
        fontSize: '0.85rem',
        color: '#4b5563',
        zIndex: 1,
      }}>
        SimplesEditor &copy; 2026
      </footer>
    </div>
  )
}

export default App
