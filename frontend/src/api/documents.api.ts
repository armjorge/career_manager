import { apiClient, apiClientFormData, isMockMode } from '@/api/client'
import { mockDb } from '@/api/mock/store'
import type {
  CoverLetterRow,
  DownloadUrlResult,
  FileTemplate,
  GenerateDocumentPayload,
  GenerateDocumentResult,
  GenerationLog,
  GenerationOption,
  ResumeDetailsRow,
  UpdateCoverLetterPayload,
  UpdateResumeDetailsPayload,
  UpdateTemplatePayload,
} from '@/types'

export const documentsApi = {
  listResumes: (): Promise<ResumeDetailsRow[]> =>
    isMockMode ? mockDb.listResumeRows() : apiClient<ResumeDetailsRow[]>('/documents/resumes'),

  updateResume: (payload: UpdateResumeDetailsPayload): Promise<ResumeDetailsRow> =>
    isMockMode
      ? mockDb.updateResumeDetails(payload)
      : apiClient<ResumeDetailsRow>(`/documents/resumes/${payload.applicationId}`, {
          method: 'PATCH',
          body: {
            ed1: payload.ed1,
            ed2: payload.ed2,
            ed3: payload.ed3,
            ex1: payload.ex1,
            ex2: payload.ex2,
            ex3: payload.ex3,
            skills: payload.skills,
            interests: payload.interests,
            fileId: payload.fileId,
          },
        }),

  listCoverLetters: (): Promise<CoverLetterRow[]> =>
    isMockMode ? mockDb.listCoverLetterRows() : apiClient<CoverLetterRow[]>('/documents/cover-letters'),

  updateCoverLetter: (payload: UpdateCoverLetterPayload): Promise<CoverLetterRow> =>
    isMockMode
      ? mockDb.updateCoverLetter(payload)
      : apiClient<CoverLetterRow>(`/documents/cover-letters/${payload.applicationId}`, {
          method: 'PATCH',
          body: {
            header: payload.header,
            body: payload.body,
            close: payload.close,
            fileId: payload.fileId,
          },
        }),

  listTemplates: (): Promise<FileTemplate[]> =>
    isMockMode ? mockDb.listTemplates() : apiClient<FileTemplate[]>('/documents/templates'),

  uploadTemplate: (file: File): Promise<FileTemplate> => {
    const formData = new FormData()
    formData.append('file', file)
    return isMockMode
      ? mockDb.uploadTemplate(file)
      : apiClientFormData<FileTemplate>('/documents/templates/upload', formData)
  },

  updateTemplate: (payload: UpdateTemplatePayload): Promise<FileTemplate> =>
    isMockMode
      ? mockDb.updateTemplate(payload)
      : apiClient<FileTemplate>(`/documents/templates/${payload.fileId}`, {
          method: 'PATCH',
          body: {
            fileType: payload.fileType,
            langId: payload.langId,
          },
        }),

  deleteTemplate: (fileId: number): Promise<void> =>
    isMockMode
      ? mockDb.deleteTemplate(fileId)
      : apiClient<void>(`/documents/templates/${fileId}`, { method: 'DELETE' }),

  listGenerationOptions: (): Promise<GenerationOption[]> =>
    isMockMode
      ? mockDb.listGenerationOptions()
      : apiClient<GenerationOption[]>('/documents/generation-options'),

  generate: (payload: GenerateDocumentPayload): Promise<GenerateDocumentResult> =>
    isMockMode
      ? mockDb.generateDocument(payload)
      : apiClient<GenerateDocumentResult>('/documents/generate', { method: 'POST', body: payload }),

  listGenerations: (limit = 10): Promise<GenerationLog[]> =>
    isMockMode
      ? mockDb.listGenerations(limit)
      : apiClient<GenerationLog[]>(`/documents/generations?limit=${limit}`),

  getDownloadUrl: (pdfId: number): Promise<DownloadUrlResult> =>
    isMockMode
      ? mockDb.getDownloadUrl(pdfId)
      : apiClient<DownloadUrlResult>(`/documents/generations/${pdfId}/download`),
}
