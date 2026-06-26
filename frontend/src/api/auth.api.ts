import { apiClient } from '@/api/client'
import type { AuthUser } from '@/types/auth'

export interface AuthResponse {
  token: string
  user: AuthUser
}

export function signInViaApi(email: string, password: string) {
  return apiClient<AuthResponse>('/auth/sign-in', {
    method: 'POST',
    body: { email, password },
  })
}

export function signUpViaApi(name: string, email: string, password: string) {
  return apiClient<AuthResponse>('/auth/sign-up', {
    method: 'POST',
    body: { name, email, password },
  })
}
