function readFlag(value: string | undefined, fallback = false): boolean {
  if (value === undefined || value === '') return fallback
  return value.toLowerCase() === 'true' || value === '1'
}

export const env = {
  appName: import.meta.env.VITE_APP_NAME ?? 'Career Manager',
  environment: import.meta.env.VITE_ENVIRONMENT ?? 'local',
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  awsRegion: import.meta.env.VITE_AWS_REGION ?? 'us-east-1',
  cognitoUserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID ?? '',
  cognitoClientId: import.meta.env.VITE_COGNITO_USER_POOL_CLIENT_ID ?? '',
  /** Cognito hosted UI domain prefix, e.g. aws-web-app-dev-auth */
  cognitoDomain: import.meta.env.VITE_COGNITO_DOMAIN ?? '',
  enableAuth: readFlag(import.meta.env.VITE_ENABLE_AUTH, true),
  enableGoogleAuth: readFlag(import.meta.env.VITE_ENABLE_GOOGLE_AUTH, false),
  enableAnalytics: readFlag(import.meta.env.VITE_ENABLE_ANALYTICS, true),
  posthogKey: import.meta.env.VITE_POSTHOG_KEY ?? '',
  posthogHost: import.meta.env.VITE_POSTHOG_HOST ?? 'https://us.i.posthog.com',
  posthogSessionRecording: readFlag(
    import.meta.env.VITE_POSTHOG_SESSION_RECORDING,
    false,
  ),
} as const

export function isCognitoConfigured(): boolean {
  return Boolean(env.cognitoUserPoolId && env.cognitoClientId)
}

export function isHostedUiConfigured(): boolean {
  return isCognitoConfigured() && Boolean(env.cognitoDomain)
}

export function cognitoHostedUiBaseUrl(): string {
  if (!env.cognitoDomain) return ''
  return `https://${env.cognitoDomain}.auth.${env.awsRegion}.amazoncognito.com`
}

export function oauthRedirectUri(): string {
  return `${window.location.origin}/auth/callback`
}
