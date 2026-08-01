import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'

export function LoginPage() {
  const {
    signIn,
    signInWithGoogle,
    configured,
    googleEnabled,
    hostedUiConfigured,
  } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await signIn(email, password)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign-in failed')
    } finally {
      setSubmitting(false)
    }
  }

  async function onGoogle() {
    setError(null)
    setSubmitting(true)
    try {
      await signInWithGoogle()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Google sign-in failed')
      setSubmitting(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-6 py-16">
      <p className="mb-3 text-sm tracking-[0.16em] uppercase text-[var(--color-muted)]">
        AWS Web App Template
      </p>
      <h1 className="mb-2 text-3xl font-semibold tracking-tight">Sign in</h1>
      <p className="mb-8 text-[var(--color-muted)]">
        Use your email and password, or continue with a social provider.
      </p>

      {!configured && (
        <p className="mb-6 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          Cognito is not configured. Set pool and client IDs in <code>.env</code>.
        </p>
      )}

      {googleEnabled && (
        <button
          type="button"
          onClick={onGoogle}
          disabled={submitting || !configured}
          className="mb-6 w-full rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 text-sm font-medium text-[var(--color-ink)] hover:bg-black/[0.03] disabled:opacity-50"
        >
          Continue with Google
        </button>
      )}

      {!googleEnabled && hostedUiConfigured && (
        <p className="mb-6 text-sm text-[var(--color-muted)]">
          Google sign-in is available once you set Google OAuth credentials in
          infra and <code>VITE_ENABLE_GOOGLE_AUTH=true</code>.
        </p>
      )}

      <form onSubmit={onSubmit} className="space-y-4">
        <label className="block space-y-1.5">
          <span className="text-sm font-medium">Email</span>
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 outline-none ring-[var(--color-accent)] focus:ring-2"
          />
        </label>
        <label className="block space-y-1.5">
          <span className="text-sm font-medium">Password</span>
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 outline-none ring-[var(--color-accent)] focus:ring-2"
          />
        </label>
        {error && <p className="text-sm text-red-700">{error}</p>}
        <button
          type="submit"
          disabled={submitting || !configured}
          className="w-full rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-sm font-medium text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-50"
        >
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      <p className="mt-4 text-sm text-[var(--color-muted)]">
        <Link to="/forgot-password">Forgot password?</Link>
      </p>
      <p className="mt-3 text-sm text-[var(--color-muted)]">
        Need an account? <Link to="/signup">Create one</Link>
      </p>
    </main>
  )
}
