import posthog from 'posthog-js'

import { env } from '../config/env'

export function isAnalyticsEnabled(): boolean {
  return env.enableAnalytics && Boolean(env.posthogKey)
}

export function identifyUser(user: { sub: string; email: string }): void {
  if (!isAnalyticsEnabled()) return
  posthog.identify(user.sub, {
    email: user.email,
    environment: env.environment,
  })
}

export function resetAnalytics(): void {
  if (!isAnalyticsEnabled()) return
  posthog.reset()
}

export function track(
  event: string,
  properties?: Record<string, string | number | boolean | null | undefined>,
): void {
  if (!isAnalyticsEnabled()) return
  posthog.capture(event, {
    environment: env.environment,
    app_name: env.appName,
    ...properties,
  })
}

export function trackPageview(): void {
  if (!isAnalyticsEnabled()) return
  posthog.capture('$pageview')
}
