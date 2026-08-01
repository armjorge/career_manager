import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'

export function ForgotPasswordPage() {
  const { forgotPassword, confirmForgotPassword, configured } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [step, setStep] = useState<'request' | 'confirm'>('request')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function onRequest(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await forgotPassword(email)
      setStep('confirm')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start recovery')
    } finally {
      setSubmitting(false)
    }
  }

  async function onConfirm(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await confirmForgotPassword(email, code, newPassword)
      navigate('/login')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not reset password')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-6 py-16">
      <h1 className="mb-2 text-3xl font-semibold tracking-tight">Reset password</h1>
      <p className="mb-8 text-[var(--color-muted)]">
        We will email a verification code to recover your account.
      </p>

      {step === 'request' ? (
        <form onSubmit={onRequest} className="space-y-4">
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
          {error && <p className="text-sm text-red-700">{error}</p>}
          <button
            type="submit"
            disabled={submitting || !configured}
            className="w-full rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-sm font-medium text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-50"
          >
            {submitting ? 'Sending…' : 'Send reset code'}
          </button>
        </form>
      ) : (
        <form onSubmit={onConfirm} className="space-y-4">
          <p className="text-sm text-[var(--color-muted)]">
            Enter the code sent to <strong>{email}</strong> and choose a new
            password (min 12 chars, mixed case, number, symbol).
          </p>
          <label className="block space-y-1.5">
            <span className="text-sm font-medium">Verification code</span>
            <input
              type="text"
              required
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 outline-none ring-[var(--color-accent)] focus:ring-2"
            />
          </label>
          <label className="block space-y-1.5">
            <span className="text-sm font-medium">New password</span>
            <input
              type="password"
              required
              minLength={12}
              autoComplete="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full rounded-md border border-[var(--color-border)] bg-white px-3 py-2 outline-none ring-[var(--color-accent)] focus:ring-2"
            />
          </label>
          {error && <p className="text-sm text-red-700">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-[var(--color-accent)] px-4 py-2.5 text-sm font-medium text-white hover:bg-[var(--color-accent-hover)] disabled:opacity-50"
          >
            {submitting ? 'Updating…' : 'Update password'}
          </button>
        </form>
      )}

      <p className="mt-6 text-sm text-[var(--color-muted)]">
        <Link to="/login">Back to sign in</Link>
      </p>
    </main>
  )
}
