import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { env, isCognitoConfigured, isHostedUiConfigured } from '../config/env'
import {
  identifyUser,
  resetAnalytics,
  track,
} from '../lib/analytics'
import {
  completeOAuthCallback,
  confirmForgotPassword,
  confirmSignUp,
  forgotPassword,
  getCurrentSession,
  getIdToken,
  hostedUiSignOut,
  sessionToUser,
  signIn,
  signOut as cognitoSignOut,
  signUp,
  startHostedUiSignIn,
  type AuthUser,
} from './cognito'

type AuthContextValue = {
  user: AuthUser | null
  loading: boolean
  configured: boolean
  enabled: boolean
  hostedUiConfigured: boolean
  googleEnabled: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<void>
  confirmSignUp: (email: string, code: string) => Promise<void>
  forgotPassword: (email: string) => Promise<void>
  confirmForgotPassword: (
    email: string,
    code: string,
    newPassword: string,
  ) => Promise<void>
  signInWithGoogle: () => Promise<void>
  signInWithHostedUi: () => Promise<void>
  completeOAuth: (code: string) => Promise<void>
  signOut: () => void
  getAccessToken: () => Promise<string | null>
}

const AuthContext = createContext<AuthContextValue | null>(null)

type Props = {
  children: ReactNode
}

export function AuthProvider({ children }: Props) {
  const enabled = env.enableAuth
  const configured = isCognitoConfigured()
  const hostedUiConfigured = isHostedUiConfigured()
  const googleEnabled = hostedUiConfigured && env.enableGoogleAuth
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(enabled && configured)

  useEffect(() => {
    if (!enabled || !configured) {
      setLoading(false)
      return
    }

    let cancelled = false

    getCurrentSession()
      .then((session) => {
        if (!cancelled && session) {
          const next = sessionToUser(session)
          setUser(next)
          identifyUser(next)
        }
      })
      .catch(() => {
        if (!cancelled) setUser(null)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [enabled, configured])

  const handleSignIn = useCallback(async (email: string, password: string) => {
    const session = await signIn(email, password)
    const next = sessionToUser(session)
    setUser(next)
    identifyUser(next)
    track('user_signed_in', { method: 'password' })
  }, [])

  const handleSignUp = useCallback(async (email: string, password: string) => {
    await signUp(email, password)
    track('user_signed_up', { method: 'password' })
  }, [])

  const handleConfirm = useCallback(async (email: string, code: string) => {
    await confirmSignUp(email, code)
    track('user_confirmed_signup')
  }, [])

  const handleForgotPassword = useCallback(async (email: string) => {
    await forgotPassword(email)
    track('password_reset_requested')
  }, [])

  const handleConfirmForgotPassword = useCallback(
    async (email: string, code: string, newPassword: string) => {
      await confirmForgotPassword(email, code, newPassword)
      track('password_reset_completed')
    },
    [],
  )

  const handleGoogle = useCallback(async () => {
    track('oauth_redirect_started', { provider: 'Google' })
    await startHostedUiSignIn('Google')
  }, [])

  const handleHostedUi = useCallback(async () => {
    track('oauth_redirect_started', { provider: 'COGNITO' })
    await startHostedUiSignIn()
  }, [])

  const handleCompleteOAuth = useCallback(async (code: string) => {
    const session = await completeOAuthCallback(code)
    const next = sessionToUser(session)
    setUser(next)
    identifyUser(next)
    track('user_signed_in', { method: 'oauth' })
  }, [])

  const handleSignOut = useCallback(() => {
    track('user_signed_out')
    resetAnalytics()
    if (hostedUiConfigured) {
      hostedUiSignOut()
      return
    }
    cognitoSignOut()
    setUser(null)
  }, [hostedUiConfigured])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      configured,
      enabled,
      hostedUiConfigured,
      googleEnabled,
      signIn: handleSignIn,
      signUp: handleSignUp,
      confirmSignUp: handleConfirm,
      forgotPassword: handleForgotPassword,
      confirmForgotPassword: handleConfirmForgotPassword,
      signInWithGoogle: handleGoogle,
      signInWithHostedUi: handleHostedUi,
      completeOAuth: handleCompleteOAuth,
      signOut: handleSignOut,
      getAccessToken: getIdToken,
    }),
    [
      user,
      loading,
      configured,
      enabled,
      hostedUiConfigured,
      googleEnabled,
      handleSignIn,
      handleSignUp,
      handleConfirm,
      handleForgotPassword,
      handleConfirmForgotPassword,
      handleGoogle,
      handleHostedUi,
      handleCompleteOAuth,
      handleSignOut,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
