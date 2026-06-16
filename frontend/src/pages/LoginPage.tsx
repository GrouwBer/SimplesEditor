import { useState, FormEvent } from 'react'
import { useAuth } from '../AuthContext'

export default function LoginPage() {
  const { signIn, signUp } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [isSignUp, setIsSignUp] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const action = isSignUp ? signUp : signIn
    const errMsg = await action(email, password)

    if (errMsg) {
      setError(errMsg)
    }
    setLoading(false)
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#0b0f19',
      fontFamily: 'Inter, system-ui, sans-serif',
    }}>
      <form onSubmit={handleSubmit} style={{
        width: '100%',
        maxWidth: '380px',
        padding: '2rem',
        backgroundColor: '#161b22',
        borderRadius: '8px',
        border: '1px solid rgba(255,255,255,0.06)',
      }}>
        <h1 style={{
          fontSize: '1.25rem',
          fontWeight: 700,
          margin: '0 0 0.25rem',
          color: '#f3f4f6',
          textAlign: 'center',
        }}>
          SIMPLES Editor
        </h1>
        <p style={{
          fontSize: '0.8rem',
          color: '#6b7280',
          textAlign: 'center',
          marginBottom: '1.5rem',
        }}>
          {isSignUp ? 'Crie sua conta' : 'Faça login para continuar'}
        </p>

        {error && (
          <div style={{
            padding: '0.5rem',
            marginBottom: '1rem',
            backgroundColor: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: '4px',
            color: '#ef4444',
            fontSize: '0.8rem',
            textAlign: 'center',
          }}>
            {error}
          </div>
        )}

        <div style={{ marginBottom: '1rem' }}>
          <label style={{
            display: 'block',
            fontSize: '0.75rem',
            color: '#9ca3af',
            marginBottom: '0.25rem',
          }}>
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            style={{
              width: '100%',
              padding: '0.5rem',
              backgroundColor: '#0d1117',
              border: '1px solid #30363d',
              borderRadius: '4px',
              color: '#f3f4f6',
              fontSize: '0.875rem',
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{
            display: 'block',
            fontSize: '0.75rem',
            color: '#9ca3af',
            marginBottom: '0.25rem',
          }}>
            Senha
          </label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            minLength={6}
            style={{
              width: '100%',
              padding: '0.5rem',
              backgroundColor: '#0d1117',
              border: '1px solid #30363d',
              borderRadius: '4px',
              color: '#f3f4f6',
              fontSize: '0.875rem',
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            padding: '0.5rem',
            backgroundColor: loading ? '#4b5563' : '#6366f1',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            fontSize: '0.875rem',
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Aguarde...' : (isSignUp ? 'CRIAR CONTA' : 'ENTRAR')}
        </button>

        <p style={{
          marginTop: '1rem',
          fontSize: '0.75rem',
          color: '#6b7280',
          textAlign: 'center',
        }}>
          {isSignUp ? 'Já tem conta?' : 'Não tem conta?'}{' '}
          <button
            type="button"
            onClick={() => { setIsSignUp(!isSignUp); setError(null) }}
            style={{
              background: 'none',
              border: 'none',
              color: '#6366f1',
              cursor: 'pointer',
              fontSize: '0.75rem',
              textDecoration: 'underline',
              padding: 0,
            }}
          >
            {isSignUp ? 'Fazer login' : 'Cadastre-se'}
          </button>
        </p>
      </form>
    </div>
  )
}
