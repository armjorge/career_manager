import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { documentsApi } from '@/api/documents.api'
import type {
  GenerateDocumentPayload,
  UpdateCoverLetterPayload,
  UpdateResumeDetailsPayload,
  UpdateTemplatePayload,
} from '@/types'

export const documentKeys = {
  resumes: ['documents', 'resumes'] as const,
  coverLetters: ['documents', 'cover-letters'] as const,
  templates: ['documents', 'templates'] as const,
  generationOptions: ['documents', 'generation-options'] as const,
  generations: ['documents', 'generations'] as const,
}

export function useResumeRows() {
  return useQuery({
    queryKey: documentKeys.resumes,
    queryFn: documentsApi.listResumes,
  })
}

export function useUpdateResumeDetails() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UpdateResumeDetailsPayload) => documentsApi.updateResume(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: documentKeys.resumes })
      void queryClient.invalidateQueries({ queryKey: documentKeys.generationOptions })
    },
  })
}

export function useCoverLetterRows() {
  return useQuery({
    queryKey: documentKeys.coverLetters,
    queryFn: documentsApi.listCoverLetters,
  })
}

export function useUpdateCoverLetter() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UpdateCoverLetterPayload) => documentsApi.updateCoverLetter(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: documentKeys.coverLetters })
      void queryClient.invalidateQueries({ queryKey: documentKeys.generationOptions })
    },
  })
}

export function useTemplates() {
  return useQuery({
    queryKey: documentKeys.templates,
    queryFn: documentsApi.listTemplates,
  })
}

export function useUploadTemplate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (file: File) => documentsApi.uploadTemplate(file),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: documentKeys.templates })
    },
  })
}

export function useUpdateTemplate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UpdateTemplatePayload) => documentsApi.updateTemplate(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: documentKeys.templates })
      void queryClient.invalidateQueries({ queryKey: documentKeys.generationOptions })
    },
  })
}

export function useDeleteTemplate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (fileId: number) => documentsApi.deleteTemplate(fileId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: documentKeys.templates })
      void queryClient.invalidateQueries({ queryKey: documentKeys.generationOptions })
    },
  })
}

export function useGenerationOptions() {
  return useQuery({
    queryKey: documentKeys.generationOptions,
    queryFn: documentsApi.listGenerationOptions,
  })
}

export function useGenerateDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: GenerateDocumentPayload) => documentsApi.generate(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: documentKeys.generations })
    },
  })
}

export function useGenerations(limit = 10) {
  return useQuery({
    queryKey: [...documentKeys.generations, limit],
    queryFn: () => documentsApi.listGenerations(limit),
  })
}

export function useDownloadGeneration() {
  return useMutation({
    mutationFn: (pdfId: number) => documentsApi.getDownloadUrl(pdfId),
  })
}

export function useDeleteGeneration() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (pdfId: number) => documentsApi.deleteGeneration(pdfId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: documentKeys.generations })
    },
  })
}
