/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_NAME?: string
  readonly VITE_ENVIRONMENT?: string
  readonly VITE_API_BASE_URL?: string
  readonly VITE_AWS_REGION?: string
  readonly VITE_COGNITO_USER_POOL_ID?: string
  readonly VITE_COGNITO_USER_POOL_CLIENT_ID?: string
  readonly VITE_COGNITO_DOMAIN?: string
  readonly VITE_ENABLE_AUTH?: string
  readonly VITE_ENABLE_GOOGLE_AUTH?: string
  readonly VITE_ENABLE_ANALYTICS?: string
  readonly VITE_POSTHOG_KEY?: string
  readonly VITE_POSTHOG_HOST?: string
  readonly VITE_POSTHOG_SESSION_RECORDING?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
