import { Navigate, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'

import { useAuth } from './useAuth'

type Props = {
  children: ReactNode
}

export function RequireAuth({ children }: Props) {
  const { user, loading, enabled, configured } = useAuth()
  const location = useLocation()

  if (!enabled || !configured) {
    return <>{children}</>
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
