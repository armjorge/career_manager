import { isMockMode } from '@/api/client'
import { mockDb } from '@/api/mock/store'
import type {
  ApplicationWithDetails,
  CreateApplicationPayload,
  JobCategory,
  Language,
  UpdateApplicationPayload,
} from '@/types'

export const applicationsApi = {
  list: (): Promise<ApplicationWithDetails[]> =>
    isMockMode ? mockDb.listApplications() : fetch('/applications').then((r) => r.json()),

  listCategories: (): Promise<JobCategory[]> =>
    isMockMode ? mockDb.listJobCategories() : fetch('/job-categories').then((r) => r.json()),

  create: (payload: CreateApplicationPayload): Promise<ApplicationWithDetails> =>
    isMockMode
      ? mockDb.createApplication(payload)
      : fetch('/applications', { method: 'POST', body: JSON.stringify(payload) }).then((r) => r.json()),

  update: (payload: UpdateApplicationPayload): Promise<ApplicationWithDetails> =>
    isMockMode
      ? mockDb.updateApplication(payload)
      : fetch(`/applications/${payload.applicationId}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        }).then((r) => r.json()),

  getOrCreateLanguage: (name: string): Promise<Language> =>
    isMockMode
      ? mockDb.getOrCreateLanguage(name)
      : fetch('/languages', { method: 'POST', body: JSON.stringify({ language: name }) }).then((r) => r.json()),

  getOrCreateCategory: (name: string): Promise<JobCategory> =>
    isMockMode
      ? mockDb.getOrCreateJobCategory(name)
      : fetch('/job-categories', {
          method: 'POST',
          body: JSON.stringify({ categoryName: name }),
        }).then((r) => r.json()),
}
