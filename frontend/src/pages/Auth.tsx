import { useState } from 'react'
import { Rocket } from 'lucide-react'
import { SignInForm, SignUpForm } from '@neondatabase/auth-ui'
import { isAuthConfigured } from '@/auth/client'
import { Alert } from '@/components/ui/Alert'
import type { AuthMode } from '@/types/auth'

export function Auth() {
  const [mode, setMode] = useState<AuthMode>('sign-in')

  const toggleMode = (nextMode: AuthMode) => {
    setMode(nextMode)
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/15 text-primary">
            <Rocket className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-semibold text-foreground">Career Manager</h1>
          <p className="mt-1 text-sm text-muted">Gestor de candidaturas · Application pipeline</p>
        </div>

        {!isAuthConfigured ? (
          <Alert
            variant="warning"
            title="Auth not configured"
            message="Set VITE_NEON_AUTH_URL in frontend/.env using the Auth Base URL from your Neon Console."
          />
        ) : null}

        {mode === 'sign-in' ? (
          <SignInForm redirectTo="/" localization={{}} />
        ) : (
          <SignUpForm redirectTo="/" localization={{}} />
        )}

        <p className="text-center text-sm text-muted">
          {mode === 'sign-in' ? (
            <>
              ¿No tienes cuenta?{' '}
              <button
                type="button"
                className="font-medium text-primary hover:text-primary-hover"
                onClick={() => toggleMode('sign-up')}
              >
                Create account
              </button>
            </>
          ) : (
            <>
              ¿Ya tienes cuenta?{' '}
              <button
                type="button"
                className="font-medium text-primary hover:text-primary-hover"
                onClick={() => toggleMode('sign-in')}
              >
                Sign in
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  )
}
