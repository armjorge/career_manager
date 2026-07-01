import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { applicationsApi } from '@/api/applications.api'
import { companyKeys } from '@/hooks/useCompanies'
import type { CreateApplicationPayload, UpdateApplicationPayload } from '@/types'

export const applicationKeys = {
  all: ['applications'] as const,
  categories: ['job-categories'] as const,
  trackers: ['trackers'] as const,
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
      void queryClient.invalidateQueries({ queryKey: applicationKeys.trackers })
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

export function useTrackers() {
  return useQuery({
    queryKey: applicationKeys.trackers,
    queryFn: applicationsApi.listTrackers,
  })
}

export function useUpdateTracker() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: applicationsApi.updateTracker,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: applicationKeys.trackers })
    },
  })
}
