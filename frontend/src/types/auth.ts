export interface AuthUser {
  id: string
  email: string
  name?: string | null
  emailVerified?: boolean
}

export type AuthMode = 'sign-in' | 'sign-up'
