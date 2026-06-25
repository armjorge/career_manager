import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { companiesApi } from '@/api/companies.api'

export const companyKeys = {
  all: ['companies'] as const,
  types: ['company-types'] as const,
  languages: ['languages'] as const,
}

export function useCompanyTypes() {
  return useQuery({
    queryKey: companyKeys.types,
    queryFn: companiesApi.listTypes,
  })
}

export function useLanguages() {
  return useQuery({
    queryKey: companyKeys.languages,
    queryFn: companiesApi.listLanguages,
  })
}

export function useCompanies() {
  return useQuery({
    queryKey: companyKeys.all,
    queryFn: companiesApi.list,
  })
}

export function useCreateCompanyType() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: companiesApi.createType,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: companyKeys.types })
    },
  })
}

export function useCreateLanguage() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: companiesApi.createLanguage,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: companyKeys.languages })
    },
  })
}

export function useCreateCompany() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ companyName, ctypeId }: { companyName: string; ctypeId: number }) =>
      companiesApi.create(companyName, ctypeId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: companyKeys.all })
    },
  })
}
