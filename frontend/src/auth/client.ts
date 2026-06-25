import { createAuthClient } from '@neondatabase/neon-js/auth'

const authUrl = import.meta.env.VITE_NEON_AUTH_URL?.trim()

if (!authUrl) {
  console.warn(
    'VITE_NEON_AUTH_URL is not set. Authentication will not work until you configure it in .env',
  )
}

export const authClient = createAuthClient(authUrl ?? 'http://localhost:0/auth')

export const isAuthConfigured = Boolean(authUrl)
