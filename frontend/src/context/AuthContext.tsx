import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { authClient, isAuthConfigured } from '@/auth/client'
import {
  extractUserIdFromToken,
  getStoredToken,
  isTokenExpired,
  readTokenFromSession,
  setStoredToken,
} from '@/auth/tokenStorage'
import type { AuthUser } from '@/types/auth'

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function mapUser(raw: Record<string, unknown>): AuthUser {
  return {
    id: String(raw.id),
    email: String(raw.email),
    name: typeof raw.name === 'string' ? raw.name : null,
    emailVerified: Boolean(raw.emailVerified),
  }
}

async function resolveAccessToken(): Promise<string | null> {
  const sessionResult = await authClient.getSession()
  const sessionToken = readTokenFromSession(
    sessionResult.data?.session as Record<string, unknown> | undefined,
  )

  if (sessionToken) {
    return sessionToken
  }

  if ('token' in authClient && typeof authClient.token === 'function') {
    const tokenResult = await authClient.token()
    const jwtToken = tokenResult.data?.token
    if (typeof jwtToken === 'string' && jwtToken.length > 0) {
      return jwtToken
    }
  }

  return getStoredToken()
}

async function syncAuthState(): Promise<{ user: AuthUser | null; token: string | null }> {
  const sessionResult = await authClient.getSession()
  const sessionUser = sessionResult.data?.user as Record<string, unknown> | undefined

  if (!sessionUser) {
    setStoredToken(null)
    return { user: null, token: null }
  }

  const token = await resolveAccessToken()
  if (!token || isTokenExpired(token)) {
    setStoredToken(null)
    return { user: null, token: null }
  }

  const userIdFromToken = extractUserIdFromToken(token)
  const user = mapUser(sessionUser)

  if (userIdFromToken && userIdFromToken !== user.id) {
    console.warn('JWT subject does not match session user id; using session user id.')
  }

  setStoredToken(token)
  return { user, token }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(() => getStoredToken())
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!isAuthConfigured) {
      setIsLoading(false)
      return
    }

    let cancelled = false

    void syncAuthState()
      .then((state) => {
        if (cancelled) return
        setUser(state.user)
        setToken(state.token)
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const result = await authClient.signIn.email({ email, password })
    if (result.error) {
      throw new Error(result.error.message ?? 'Sign in failed')
    }

    const state = await syncAuthState()
    if (!state.user || !state.token) {
      throw new Error('Signed in, but no active session was returned.')
    }

    setUser(state.user)
    setToken(state.token)
  }, [])

  const register = useCallback(async (name: string, email: string, password: string) => {
    const result = await authClient.signUp.email({ name, email, password })
    if (result.error) {
      throw new Error(result.error.message ?? 'Sign up failed')
    }

    const state = await syncAuthState()
    if (!state.user || !state.token) {
      throw new Error('Account created, but no active session was returned. Check email verification settings.')
    }

    setUser(state.user)
    setToken(state.token)
  }, [])

  const logout = useCallback(async () => {
    await authClient.signOut()
    setStoredToken(null)
    setUser(null)
    setToken(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(user && token),
      isLoading,
      login,
      register,
      logout,
    }),
    [user, token, isLoading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
