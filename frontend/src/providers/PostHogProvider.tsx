import { useEffect, type ReactNode } from 'react'
import posthog from 'posthog-js'
import { PostHogProvider as PHProvider } from 'posthog-js/react'

import { env } from '../config/env'
import { isAnalyticsEnabled } from '../lib/analytics'

type Props = {
  children: ReactNode
}

/**
 * Global analytics wrapper. When VITE_ENABLE_ANALYTICS is false or
 * VITE_POSTHOG_KEY is empty, children render without initializing PostHog.
 *
 * With a project key set, captures:
 * - SPA pageviews / pageleaves
 * - Autocapture (clicks, form interactions)
 * - Custom auth events via lib/analytics.ts
 */
export function PostHogProvider({ children }: Props) {
  const enabled = isAnalyticsEnabled()

  useEffect(() => {
    if (!enabled) return

    posthog.init(env.posthogKey, {
      api_host: env.posthogHost,
      person_profiles: 'identified_only',
      // SPA-friendly pageviews (react-router history changes)
      capture_pageview: 'history_change',
      capture_pageleave: true,
      autocapture: true,
      persistence: 'localStorage+cookie',
      disable_session_recording: !env.posthogSessionRecording,
    })

    posthog.register({
      environment: env.environment,
      app_name: env.appName,
    })
  }, [enabled])

  if (!enabled) {
    return <>{children}</>
  }

  return <PHProvider client={posthog}>{children}</PHProvider>
}
