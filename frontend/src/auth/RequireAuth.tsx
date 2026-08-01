import { Navigate, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'

import { useAuth } from './useAuth'

type Props = {
  children: ReactNode
}

export function RequireAuth({ children }: Props) {
  const { user, loading, enabled, configured } = useAuth()
  const location = useLocation()

  // Auth disabled on purpose (local/demo) — allow through.
  if (!enabled) {
    return <>{children}</>
  }

  // Auth enabled but Cognito env vars missing from the build — never open the app.
  if (!configured) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-lg flex-col justify-center gap-3 px-6">
        <h1 className="text-xl font-semibold text-foreground">Auth is not configured</h1>
        <p className="text-sm text-muted">
          This build is missing Cognito settings. Set{' '}
          <code className="text-foreground">VITE_COGNITO_USER_POOL_ID</code> and{' '}
          <code className="text-foreground">VITE_COGNITO_USER_POOL_CLIENT_ID</code> in the
          GitHub Environment secrets, then rebuild/redeploy the frontend.
        </p>
      </main>
    )
  }

  if (loading) {
    return (
      <main className="mx-auto flex min-h-screen w-full max-w-md items-center justify-center px-6">
        <p className="text-muted">Checking session…</p>
      </main>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <>{children}</>
}

export function RedirectIfAuthenticated({ children }: Props) {
  const { user, loading, enabled, configured } = useAuth()

  if (enabled && configured && !loading && user) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
