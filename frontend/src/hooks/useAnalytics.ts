import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/api/analytics.api'

export const analyticsKeys = {
  summary: ['analytics', 'summary'] as const,
}

export function useAnalyticsSummary() {
  return useQuery({
    queryKey: analyticsKeys.summary,
    queryFn: analyticsApi.summary,
  })
}
