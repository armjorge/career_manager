import { apiClient } from '@/api/client'
import type { Website } from '@/types'

export interface WebsiteWithCount extends Website {
  applicationCount: number
}

export const sitesApi = {
  list: (): Promise<WebsiteWithCount[]> =>
    apiClient<WebsiteWithCount[]>('/sites'),

  create: (address: string): Promise<WebsiteWithCount> =>
    apiClient<WebsiteWithCount>('/sites', { method: 'POST', body: { address } }),

  delete: (siteId: number): Promise<void> =>
    apiClient<void>(`/sites/${siteId}`, { method: 'DELETE' }),
}
