import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { signInViaApi, signUpViaApi } from '@/api/auth.api'
import { isMockMode } from '@/api/client'
import { authClient, getJwtToken, isAuthConfigured } from '@/auth/client'
import {
  extractTokenFromAuthData,
  getStoredToken,
  isUsableToken,
  setStoredToken,
  userFromToken,
} from '@/auth/tokenStorage'
import type { AuthUser } from '@/types/auth'

interface AuthContextValue {
  user: AuthUser | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)
const AUTH_REQUEST_TIMEOUT_MS = 15_000

function withTimeout<T>(promise: Promise<T>, timeoutMs: number, label: string): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = window.setTimeout(() => {
      reject(new Error(`${label} timed out after ${timeoutMs}ms`))
    }, timeoutMs)

    promise
      .then((value) => {
        window.clearTimeout(timer)
        resolve(value)
      })
      .catch((error: unknown) => {
        window.clearTimeout(timer)
        reject(error)
      })
  })
}

function mapUser(raw: Record<string, unknown>): AuthUser {
  return {
    id: String(raw.id),
    email: String(raw.email),
    name: typeof raw.name === 'string' ? raw.name : null,
    emailVerified: Boolean(raw.emailVerified),
  }
}

async function fetchAuthToken(signInData?: Record<string, unknown>): Promise<string | null> {
  const fromSignIn = extractTokenFromAuthData(signInData)
  if (fromSignIn && isUsableToken(fromSignIn)) {
    return fromSignIn
  }

  const sessionResult = await authClient.getSession()
  const session = sessionResult.data?.session as Record<string, unknown> | undefined
  const fromSession = extractTokenFromAuthData({ session })
  if (fromSession && isUsableToken(fromSession)) {
    return fromSession
  }

  if ('token' in authClient && typeof authClient.token === 'function') {
    const tokenResult = await authClient.token()
    const jwtToken = tokenResult.data?.token
    if (typeof jwtToken === 'string' && jwtToken.length > 0 && isUsableToken(jwtToken)) {
      return jwtToken
    }
  }

  const jwt = await getJwtToken()
  if (jwt && isUsableToken(jwt)) {
    return jwt
  }

  return null
}

async function establishSessionFromSignIn(
  signInData?: Record<string, unknown>,
): Promise<{ user: AuthUser; token: string }> {
  const token = await withTimeout(
    fetchAuthToken(signInData),
    AUTH_REQUEST_TIMEOUT_MS,
    'Auth token request',
  )

  if (!token || !isUsableToken(token)) {
    throw new Error('Signed in, but no valid access token was returned.')
  }

  const sessionUser = signInData?.user as Record<string, unknown> | undefined
  const user = sessionUser ? mapUser(sessionUser) : userFromToken(token)
  if (!user) {
    throw new Error('Signed in, but user details could not be resolved from the token.')
  }

  setStoredToken(token)
  return { user, token }
}

function applyAuthSession(user: AuthUser, token: string) {
  if (!isUsableToken(token)) {
    throw new Error('Signed in, but no valid access token was returned.')
  }
  setStoredToken(token)
  return { user, token }
}

function restoreSessionFromStorage(): { user: AuthUser; token: string } | null {
  const storedToken = getStoredToken()
  if (!isUsableToken(storedToken)) {
    setStoredToken(null)
    return null
  }

  const user = userFromToken(storedToken)
  if (!user) {
    setStoredToken(null)
    return null
  }

  return { user, token: storedToken }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const initialSession = restoreSessionFromStorage()
  const [user, setUser] = useState<AuthUser | null>(initialSession?.user ?? null)
  const [token, setToken] = useState<string | null>(initialSession?.token ?? null)

  useEffect(() => {
    const stored = restoreSessionFromStorage()
    if (stored) {
      setUser(stored.user)
      setToken(stored.token)
      return
    }
    // Pick up sessions established by auth-ui (OAuth redirects, etc.)
    void fetchAuthToken().then((token) => {
      if (!token) return
      const user = userFromToken(token)
      if (user) {
        setStoredToken(token)
        setUser(user)
        setToken(token)
      }
    })
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    if (!isAuthConfigured) {
      throw new Error('Authentication is not configured.')
    }

    if (isMockMode) {
      const result = await withTimeout(
        authClient.signIn.email({ email, password }),
        AUTH_REQUEST_TIMEOUT_MS,
        'Sign in',
      )
      if (result.error) {
        throw new Error(result.error.message ?? 'Sign in failed')
      }

      const state = await establishSessionFromSignIn(result.data as Record<string, unknown> | undefined)
      setUser(state.user)
      setToken(state.token)
      return
    }

    const data = await withTimeout(signInViaApi(email, password), AUTH_REQUEST_TIMEOUT_MS, 'Sign in')
    const state = applyAuthSession(data.user, data.token)
    setUser(state.user)
    setToken(state.token)
  }, [])

  const register = useCallback(async (name: string, email: string, password: string) => {
    if (!isAuthConfigured) {
      throw new Error('Authentication is not configured.')
    }

    if (isMockMode) {
      const result = await withTimeout(
        authClient.signUp.email({ name, email, password }),
        AUTH_REQUEST_TIMEOUT_MS,
        'Sign up',
      )
      if (result.error) {
        throw new Error(result.error.message ?? 'Sign up failed')
      }

      const state = await establishSessionFromSignIn(result.data as Record<string, unknown> | undefined)
      setUser(state.user)
      setToken(state.token)
      return
    }

    const data = await withTimeout(
      signUpViaApi(name, email, password),
      AUTH_REQUEST_TIMEOUT_MS,
      'Sign up',
    )
    const state = applyAuthSession(data.user, data.token)
    setUser(state.user)
    setToken(state.token)
  }, [])

  const logout = useCallback(async () => {
    try {
      await withTimeout(authClient.signOut(), AUTH_REQUEST_TIMEOUT_MS, 'Sign out')
    } catch (error: unknown) {
      console.warn('Sign out request failed; clearing local session anyway.', error)
    } finally {
      setStoredToken(null)
      setUser(null)
      setToken(null)
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(user && token),
      login,
      register,
      logout,
    }),
    [user, token, login, register, logout],
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
