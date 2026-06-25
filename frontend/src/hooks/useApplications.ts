import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { applicationsApi } from '@/api/applications.api'
import { companyKeys } from '@/hooks/useCompanies'
import type { CreateApplicationPayload, UpdateApplicationPayload } from '@/types'

export const applicationKeys = {
  all: ['applications'] as const,
  categories: ['job-categories'] as const,
}

export function useApplications() {
  return useQuery({
    queryKey: applicationKeys.all,
    queryFn: applicationsApi.list,
  })
}

export function useJobCategories() {
  return useQuery({
    queryKey: applicationKeys.categories,
    queryFn: applicationsApi.listCategories,
  })
}

export function useCreateApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateApplicationPayload) => applicationsApi.create(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: applicationKeys.all })
    },
  })
}

export function useUpdateApplication() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: UpdateApplicationPayload) => applicationsApi.update(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: applicationKeys.all })
    },
  })
}

export function useResolveLanguage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: applicationsApi.getOrCreateLanguage,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: companyKeys.languages })
    },
  })
}

export function useResolveCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: applicationsApi.getOrCreateCategory,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: applicationKeys.categories })
    },
  })
}
