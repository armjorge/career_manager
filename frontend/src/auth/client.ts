import { createInternalNeonAuth } from '@neondatabase/neon-js/auth'

const authUrl = import.meta.env.VITE_NEON_AUTH_URL?.trim()

if (!authUrl) {
  console.warn(
    'VITE_NEON_AUTH_URL is not set. Authentication will not work until you configure it in .env',
  )
}

const neonAuth = createInternalNeonAuth(authUrl ?? 'http://localhost:0/auth', {
  fetchOptions: {
    credentials: 'include',
  },
})

export const authClient = neonAuth.adapter
export const getJwtToken = neonAuth.getJWTToken
export const isAuthConfigured = Boolean(authUrl)
