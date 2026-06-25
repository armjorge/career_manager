const TOKEN_STORAGE_KEY = 'career_manager.auth.token'

export interface JwtPayload {
  sub?: string
  exp?: number
  iat?: number
  [key: string]: unknown
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
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
  const payload = decodeJwtPayload(token)
  if (!payload?.exp) return false
  return payload.exp * 1000 <= Date.now()
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
