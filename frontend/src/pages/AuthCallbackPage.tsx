import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { readOAuthState } from '../auth/oauth'

export function AuthCallbackPage() {
  const { completeOAuth } = useAuth()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const code = params.get('code')
    const state = params.get('state')
    const oauthError = params.get('error_description') || params.get('error')

    if (oauthError) {
      setError(oauthError)
      return
    }

    if (!code) {
      setError('Missing authorization code.')
      return
    }

    const expectedState = readOAuthState()
    if (expectedState && state && expectedState !== state) {
      setError('OAuth state mismatch. Please try signing in again.')
      return
    }

    let cancelled = false
    completeOAuth(code)
      .then(() => {
        if (!cancelled) navigate('/', { replace: true })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'OAuth sign-in failed')
        }
      })

    return () => {
      cancelled = true
    }
  }, [completeOAuth, navigate, params])

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-6 py-16">
      <h1 className="mb-2 text-3xl font-semibold tracking-tight">Completing sign-in</h1>
      {error ? (
        <div className="space-y-4">
          <p className="text-sm text-red-700">{error}</p>
          <button
            type="button"
            onClick={() => navigate('/login', { replace: true })}
            className="rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white"
          >
            Back to sign in
          </button>
        </div>
      ) : (
        <p className="text-[var(--color-muted)]">Finishing authentication…</p>
      )}
    </main>
  )
}
