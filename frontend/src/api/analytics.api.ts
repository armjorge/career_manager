import { apiClient, isMockMode } from '@/api/client'
import { mockDb } from '@/api/mock/store'
import type { AnalyticsSummary } from '@/types'

export const analyticsApi = {
  summary: (): Promise<AnalyticsSummary> =>
    isMockMode ? mockDb.getAnalyticsSummary() : apiClient<AnalyticsSummary>('/analytics/summary'),
}
