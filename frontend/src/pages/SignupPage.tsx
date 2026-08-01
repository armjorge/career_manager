import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'

export function SignupPage() {
  const { signUp, confirmSignUp, configured } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [code, setCode] = useState('')
  const [step, setStep] = useState<'register' | 'confirm'>('register')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function onRegister(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await signUp(email, password)
      setStep('confirm')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign-up failed')
    } finally {
      setSubmitting(false)
    }
  }

  async function onConfirm(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await confirmSignUp(email, code)
      navigate('/login')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Confirmation failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-6 py-16">
      <h1 className="mb-2 text-3xl font-semibold tracking-tight">Create account</h1>
      <p className="mb-8 text-[var(--color-muted)]">
        Password must be at least 12 characters with upper, lower, number, and
        symbol.
      </p>

      {step === 'register' ? (
        <form onSubmit={onRegister} className="space-y-4">
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
              minLength={12}
              autoComplete="new-password"
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
            {submitting ? 'Creating…' : 'Create account'}
          </button>
        </form>
      ) : (
        <form onSubmit={onConfirm} className="space-y-4">
          <p className="text-sm text-[var(--color-muted)]">
            Enter the verification code emailed to <strong>{email}</strong>.
          </p>
          <label className="block space-y-1.5">
            <span className="text-sm font-medium">Confirmation code</span>
            <input
              type="text"
              required
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 outline-none ring-[var(--color-accent)] focus:ring-2"
            />
          </label>
          {error && <p className="text-sm text-red-700">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-sm font-medium text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-50"
          >
            {submitting ? 'Confirming…' : 'Confirm account'}
          </button>
        </form>
      )}

      <p className="mt-6 text-sm text-[var(--color-muted)]">
        Already registered? <Link to="/login">Sign in</Link>
      </p>
    </main>
  )
}
