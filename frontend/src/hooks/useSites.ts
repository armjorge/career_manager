import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { sitesApi } from '@/api/sites.api'
import { applicationKeys } from '@/hooks/useApplications'

export const siteKeys = {
  all: ['sites'] as const,
}

export function useSites() {
  return useQuery({
    queryKey: siteKeys.all,
    queryFn: sitesApi.list,
  })
}

export function useCreateSite() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (address: string) => sitesApi.create(address),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: siteKeys.all })
    },
  })
}

export function useDeleteSite() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (siteId: number) => sitesApi.delete(siteId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: siteKeys.all })
      void queryClient.invalidateQueries({ queryKey: applicationKeys.all })
    },
  })
}
