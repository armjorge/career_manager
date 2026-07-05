import { apiClient, isMockMode } from '@/api/client'
import { mockDb } from '@/api/mock/store'
import type { Website } from '@/types'

export interface WebsiteWithCount extends Website {
  applicationCount: number
}

export const sitesApi = {
  list: (): Promise<WebsiteWithCount[]> =>
    isMockMode ? mockDb.listWebsites() : apiClient<WebsiteWithCount[]>('/sites'),

  create: (address: string): Promise<WebsiteWithCount> =>
    isMockMode
      ? mockDb.createWebsite(address)
      : apiClient<WebsiteWithCount>('/sites', { method: 'POST', body: { address } }),

  delete: (siteId: number): Promise<void> =>
    isMockMode
      ? mockDb.deleteWebsite(siteId)
      : apiClient<void>(`/sites/${siteId}`, { method: 'DELETE' }),
}
