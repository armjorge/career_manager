import { apiClient, isMockMode } from '@/api/client'
import { mockDb } from '@/api/mock/store'
import type {
  ApplicationWithDetails,
  CreateApplicationPayload,
  JobCategory,
  Language,
  TrackerWithDetails,
  UpdateApplicationPayload,
  UpdateTrackerPayload,
} from '@/types'

export const applicationsApi = {
  list: (): Promise<ApplicationWithDetails[]> =>
    isMockMode ? mockDb.listApplications() : apiClient<ApplicationWithDetails[]>('/applications'),

  listCategories: (): Promise<JobCategory[]> =>
    isMockMode ? mockDb.listJobCategories() : apiClient<JobCategory[]>('/job-categories'),

  create: (payload: CreateApplicationPayload): Promise<ApplicationWithDetails> =>
    isMockMode
      ? mockDb.createApplication(payload)
      : apiClient<ApplicationWithDetails>('/applications', {
          method: 'POST',
          body: {
            companyId: payload.companyId,
            jobName: payload.jobName,
            langId: payload.langId,
            status: payload.status,
            jobCatId: payload.jobCatId,
            siteId: payload.siteId,
          },
        }),

  update: (payload: UpdateApplicationPayload): Promise<ApplicationWithDetails> =>
    isMockMode
      ? mockDb.updateApplication(payload)
      : apiClient<ApplicationWithDetails>(`/applications/${payload.applicationId}`, {
          method: 'PUT',
          body: {
            applicationId: payload.applicationId,
            companyId: payload.companyId,
            jobName: payload.jobName,
            langId: payload.langId,
            status: payload.status,
            jobCatId: payload.jobCatId,
            siteId: payload.siteId,
          },
        }),

  getOrCreateLanguage: (name: string): Promise<Language> =>
    isMockMode
      ? mockDb.getOrCreateLanguage(name)
      : apiClient<Language>('/languages/resolve', { method: 'POST', body: { language: name } }),

  getOrCreateCategory: (name: string): Promise<JobCategory> =>
    isMockMode
      ? mockDb.getOrCreateJobCategory(name)
      : apiClient<JobCategory>('/job-categories/resolve', {
          method: 'POST',
          body: { categoryName: name },
        }),

  listTrackers: (): Promise<TrackerWithDetails[]> =>
    isMockMode ? mockDb.listTrackers() : apiClient<TrackerWithDetails[]>('/trackers'),

  updateTracker: (payload: UpdateTrackerPayload): Promise<TrackerWithDetails> =>
    isMockMode
      ? mockDb.updateTracker(payload)
      : apiClient<TrackerWithDetails>(`/trackers/${payload.applicationId}`, {
          method: 'PUT',
          body: {
            contactName: payload.contactName,
            contactEmail: payload.contactEmail,
            positionUrl: payload.positionUrl,
          },
        }),
}
