import { isMockMode } from '@/api/client'
import { mockDb } from '@/api/mock/store'
import type { Company, CompanyType, Language } from '@/types'

export const companiesApi = {
  listTypes: (): Promise<CompanyType[]> =>
    isMockMode ? mockDb.listCompanyTypes() : fetch('/company-types').then((r) => r.json()),

  createType: (typeName: string): Promise<CompanyType> =>
    isMockMode
      ? mockDb.createCompanyType(typeName)
      : fetch('/company-types', {
          method: 'POST',
          body: JSON.stringify({ typeName }),
        }).then((r) => r.json()),

  listLanguages: (): Promise<Language[]> =>
    isMockMode ? mockDb.listLanguages() : fetch('/languages').then((r) => r.json()),

  createLanguage: (language: string): Promise<Language> =>
    isMockMode
      ? mockDb.createLanguage(language)
      : fetch('/languages', {
          method: 'POST',
          body: JSON.stringify({ language }),
        }).then((r) => r.json()),

  list: (): Promise<Company[]> =>
    isMockMode ? mockDb.listCompanies() : fetch('/companies').then((r) => r.json()),

  create: (companyName: string, ctypeId: number): Promise<Company> =>
    isMockMode
      ? mockDb.createCompany(companyName, ctypeId)
      : fetch('/companies', {
          method: 'POST',
          body: JSON.stringify({ companyName, ctypeId }),
        }).then((r) => r.json()),
}
