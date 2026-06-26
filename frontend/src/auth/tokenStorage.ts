import type { AuthUser } from '@/types/auth'

const TOKEN_STORAGE_KEY = 'career_manager.auth.token'

export interface JwtPayload {
  sub?: string
  exp?: number
  iat?: number
  [key: string]: unknown
}

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY)
  } catch {
    return null
  }
}

export function setStoredToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token)
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
    }
  } catch {
    // Ignore storage failures (private mode / blocked storage).
  }
}

export function decodeJwtPayload(token: string): JwtPayload | null {
  try {
    const [, payloadSegment] = token.split('.')
    if (!payloadSegment) return null

    const normalized = payloadSegment.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=')
    const decoded = atob(padded)
    return JSON.parse(decoded) as JwtPayload
  } catch {
    return null
  }
}

export function extractUserIdFromToken(token: string): string | null {
  const payload = decodeJwtPayload(token)
  return typeof payload?.sub === 'string' ? payload.sub : null
}

export function isTokenExpired(token: string): boolean {
  return !isUsableToken(token)
}

export function isUsableToken(token: string | null | undefined): token is string {
  if (!token) return false
  const parts = token.split('.')
  if (parts.length !== 3) return false

  const payload = decodeJwtPayload(token)
  if (!payload?.sub) return false
  if (typeof payload.exp !== 'number') return false

  return payload.exp * 1000 > Date.now()
}

export function userFromToken(token: string): AuthUser | null {
  const payload = decodeJwtPayload(token)
  if (!payload?.sub) return null

  const name =
    typeof payload.name === 'string'
      ? payload.name
      : typeof payload.user_name === 'string'
        ? payload.user_name
        : null

  return {
    id: String(payload.sub),
    email: typeof payload.email === 'string' ? payload.email : '',
    name,
    emailVerified: Boolean(payload.email_verified ?? payload.emailVerified),
  }
}

export function readTokenFromSession(session: Record<string, unknown> | null | undefined): string | null {
  if (!session) return null

  const candidates = ['access_token', 'token', 'accessToken']
  for (const key of candidates) {
    const value = session[key]
    if (typeof value === 'string' && value.length > 0) {
      return value
    }
  }

  return null
}
