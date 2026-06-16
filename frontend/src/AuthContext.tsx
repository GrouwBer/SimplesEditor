import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'

interface User {
  id: string
  email: string
}

interface Session {
  access_token: string
  refresh_token?: string
}

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<string | null>
  signUp: (email: string, password: string) => Promise<string | null>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const API_BASE = '/api/auth'

function getStoredSession(): Session | null {
  try {
    const stored = localStorage.getItem('simples_session')
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

function storeSession(session: Session | null) {
  if (session) {
    localStorage.setItem('simples_session', JSON.stringify(session))
  } else {
    localStorage.removeItem('simples_session')
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(getStoredSession)
  const [loading, setLoading] = useState(true)

  // Verifica sessao ao montar
  useEffect(() => {
    if (session?.access_token) {
      fetch(`${API_BASE}/me`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      })
        .then(res => {
          if (!res.ok) throw new Error('Sessão expirada')
          return res.json()
        })
        .then(data => {
          setUser({ id: data.user_id, email: data.email })
        })
        .catch(() => {
          setSession(null)
          setUser(null)
          storeSession(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const signIn = useCallback(async (email: string, password: string): Promise<string | null> => {
    try {
      const res = await fetch(`${API_BASE}/signin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) return data.error || 'Erro ao fazer login'
      setSession(data.session)
      setUser(data.user)
      storeSession(data.session)
      return null
    } catch {
      return 'Erro de conexão com o servidor'
    }
  }, [])

  const signUp = useCallback(async (email: string, password: string): Promise<string | null> => {
    try {
      const res = await fetch(`${API_BASE}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) return data.error || 'Erro ao cadastrar'
      if (data.session) {
        setSession(data.session)
        setUser(data.user)
        storeSession(data.session)
      }
      return null
    } catch {
      return 'Erro de conexão com o servidor'
    }
  }, [])

  const signOut = useCallback(async () => {
    if (session?.access_token) {
      try {
        await fetch(`${API_BASE}/signout`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${session.access_token}` },
        })
      } catch { /* ignore */ }
    }
    setSession(null)
    setUser(null)
    storeSession(null)
  }, [session])

  return (
    <AuthContext.Provider value={{ user, session, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth deve ser usado dentro de AuthProvider')
  return context
}
