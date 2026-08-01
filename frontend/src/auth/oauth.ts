import { cognitoHostedUiBaseUrl, env } from '../config/env'

const PKCE_VERIFIER_KEY = 'cognito_pkce_verifier'
const PKCE_STATE_KEY = 'cognito_oauth_state'

function base64UrlEncode(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (const byte of bytes) {
    binary += String.fromCharCode(byte)
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

function randomString(byteLength = 32): string {
  const bytes = new Uint8Array(byteLength)
  crypto.getRandomValues(bytes)
  return base64UrlEncode(bytes.buffer)
}

async function sha256Base64Url(value: string): Promise<string> {
  const data = new TextEncoder().encode(value)
  const digest = await crypto.subtle.digest('SHA-256', data)
  return base64UrlEncode(digest)
}

export type AuthorizeParams = {
  redirectUri: string
  identityProvider?: 'Google' | 'COGNITO'
}

export async function buildAuthorizeUrl(
  params: AuthorizeParams,
): Promise<{ url: string; state: string; verifier: string }> {
  const verifier = randomString(32)
  const challenge = await sha256Base64Url(verifier)
  const state = randomString(16)

  sessionStorage.setItem(PKCE_VERIFIER_KEY, verifier)
  sessionStorage.setItem(PKCE_STATE_KEY, state)

  const search = new URLSearchParams({
    client_id: env.cognitoClientId,
    response_type: 'code',
    scope: 'openid email profile',
    redirect_uri: params.redirectUri,
    state,
    code_challenge_method: 'S256',
    code_challenge: challenge,
  })

  if (params.identityProvider) {
    search.set('identity_provider', params.identityProvider)
  }

  return {
    url: `${cognitoHostedUiBaseUrl()}/oauth2/authorize?${search.toString()}`,
    state,
    verifier,
  }
}

export function clearPkceSession(): void {
  sessionStorage.removeItem(PKCE_VERIFIER_KEY)
  sessionStorage.removeItem(PKCE_STATE_KEY)
}

export function readPkceVerifier(): string | null {
  return sessionStorage.getItem(PKCE_VERIFIER_KEY)
}

export function readOAuthState(): string | null {
  return sessionStorage.getItem(PKCE_STATE_KEY)
}

export type TokenResponse = {
  id_token: string
  access_token: string
  refresh_token?: string
  expires_in: number
  token_type: string
}

export async function exchangeAuthorizationCode(
  code: string,
  redirectUri: string,
): Promise<TokenResponse> {
  const verifier = readPkceVerifier()
  if (!verifier) {
    throw new Error('Missing PKCE verifier. Restart sign-in from the login page.')
  }

  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    client_id: env.cognitoClientId,
    code,
    redirect_uri: redirectUri,
    code_verifier: verifier,
  })

  const response = await fetch(`${cognitoHostedUiBaseUrl()}/oauth2/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Token exchange failed (${response.status})`)
  }

  return (await response.json()) as TokenResponse
}
