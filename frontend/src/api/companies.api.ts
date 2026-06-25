import { apiClient, isMockMode } from '@/api/client'
import { mockDb } from '@/api/mock/store'
import type { Company, CompanyType, Language } from '@/types'

export const companiesApi = {
  listTypes: (): Promise<CompanyType[]> =>
    isMockMode ? mockDb.listCompanyTypes() : apiClient<CompanyType[]>('/company-types'),

  createType: (typeName: string): Promise<CompanyType> =>
    isMockMode
      ? mockDb.createCompanyType(typeName)
      : apiClient<CompanyType>('/company-types', { method: 'POST', body: { typeName } }),

  listLanguages: (): Promise<Language[]> =>
    isMockMode ? mockDb.listLanguages() : apiClient<Language[]>('/languages'),

  createLanguage: (language: string): Promise<Language> =>
    isMockMode
      ? mockDb.createLanguage(language)
      : apiClient<Language>('/languages', { method: 'POST', body: { language } }),

  list: (): Promise<Company[]> =>
    isMockMode ? mockDb.listCompanies() : apiClient<Company[]>('/companies'),

  create: (companyName: string, ctypeId: number): Promise<Company> =>
    isMockMode
      ? mockDb.createCompany(companyName, ctypeId)
      : apiClient<Company>('/companies', {
          method: 'POST',
          body: { companyName, ctypeId },
        }),
}
