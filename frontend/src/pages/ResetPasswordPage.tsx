import { AuthView } from '@neondatabase/auth-ui'

export function ResetPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-md">
        <AuthView />
      </div>
    </div>
  )
}
