import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, Rocket } from 'lucide-react'
import { isAuthConfigured } from '@/auth/client'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Field, Label } from '@/components/ui/Label'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/context/AuthContext'
import type { AuthMode } from '@/types/auth'
import {
  signInSchema,
  signUpSchema,
  type SignInFormValues,
  type SignUpFormValues,
} from '@/validators/schemas'

export function Auth() {
  const { login, register } = useAuth()
  const [mode, setMode] = useState<AuthMode>('sign-in')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const signInForm = useForm<SignInFormValues>({
    resolver: zodResolver(signInSchema),
    defaultValues: { email: '', password: '' },
  })

  const signUpForm = useForm<SignUpFormValues>({
    resolver: zodResolver(signUpSchema),
    defaultValues: { name: '', email: '', password: '' },
  })

  const toggleMode = (nextMode: AuthMode) => {
    setMode(nextMode)
    setError(null)
    signInForm.clearErrors()
    signUpForm.clearErrors()
  }

  const handleSignIn = signInForm.handleSubmit(async (values) => {
    setError(null)
    setIsSubmitting(true)
    try {
      await login(values.email, values.password)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in.')
    } finally {
      setIsSubmitting(false)
    }
  })

  const handleSignUp = signUpForm.handleSubmit(async (values) => {
    setError(null)
    setIsSubmitting(true)
    try {
      await register(values.name, values.email, values.password)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create account.')
    } finally {
      setIsSubmitting(false)
    }
  })

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

        <Card>
          <CardHeader>
            <CardTitle>{mode === 'sign-in' ? 'Sign In' : 'Create Account'}</CardTitle>
            <CardDescription>
              {mode === 'sign-in'
                ? 'Inicia sesión para acceder a tu espacio de trabajo.'
                : 'Crea una cuenta para empezar a gestionar tus candidaturas.'}
            </CardDescription>
          </CardHeader>

          {mode === 'sign-in' ? (
            <form onSubmit={handleSignIn} className="space-y-4">
              <Field>
                <Label htmlFor="sign-in-email">Email</Label>
                <Input
                  id="sign-in-email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  {...signInForm.register('email')}
                  error={signInForm.formState.errors.email?.message}
                />
              </Field>

              <Field>
                <Label htmlFor="sign-in-password">Password</Label>
                <Input
                  id="sign-in-password"
                  type="password"
                  autoComplete="current-password"
                  placeholder="••••••••"
                  {...signInForm.register('password')}
                  error={signInForm.formState.errors.password?.message}
                />
              </Field>

              {error ? <Alert variant="error" message={error} /> : null}

              <Button type="submit" className="w-full" disabled={isSubmitting || !isAuthConfigured}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleSignUp} className="space-y-4">
              <Field>
                <Label htmlFor="sign-up-name">Name</Label>
                <Input
                  id="sign-up-name"
                  type="text"
                  autoComplete="name"
                  placeholder="Your name"
                  {...signUpForm.register('name')}
                  error={signUpForm.formState.errors.name?.message}
                />
              </Field>

              <Field>
                <Label htmlFor="sign-up-email">Email</Label>
                <Input
                  id="sign-up-email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  {...signUpForm.register('email')}
                  error={signUpForm.formState.errors.email?.message}
                />
              </Field>

              <Field>
                <Label htmlFor="sign-up-password">Password</Label>
                <Input
                  id="sign-up-password"
                  type="password"
                  autoComplete="new-password"
                  placeholder="At least 8 characters"
                  {...signUpForm.register('password')}
                  error={signUpForm.formState.errors.password?.message}
                />
              </Field>

              {error ? <Alert variant="error" message={error} /> : null}

              <Button type="submit" className="w-full" disabled={isSubmitting || !isAuthConfigured}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  'Create Account'
                )}
              </Button>
            </form>
          )}

          <p className="mt-5 border-t border-border pt-4 text-center text-sm text-muted">
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
        </Card>
      </div>
    </div>
  )
}
