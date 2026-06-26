import type {
  Application,
  ApplicationWithDetails,
  Company,
  CompanyType,
  CoverLetter,
  CreateApplicationPayload,
  GenerationLog,
  JobCategory,
  Language,
  ResumeDetails,
  TrackerDetails,
  TrackerWithDetails,
  UpdateApplicationPayload,
  UpdateTrackerPayload,
  Website,
} from '@/types'
import { ApiClientError } from '@/api/client'

interface MockStore {
  companyTypes: CompanyType[]
  languages: Language[]
  companies: Company[]
  jobCategories: JobCategory[]
  applications: Application[]
  trackers: TrackerDetails[]
  resumeDetails: ResumeDetails[]
  coverLetters: CoverLetter[]
  websites: Website[]
  generationLogs: GenerationLog[]
  nextIds: Record<string, number>
}

const now = () => new Date().toISOString()

function createInitialStore(): MockStore {
  return {
    companyTypes: [
      { ctypeId: 1, typeName: 'Consulting', createdAt: now() },
      { ctypeId: 2, typeName: 'Technology', createdAt: now() },
      { ctypeId: 3, typeName: 'Finance', createdAt: now() },
    ],
    languages: [
      { langId: 1, language: 'English', createdAt: now() },
      { langId: 2, language: 'Spanish', createdAt: now() },
      { langId: 3, language: 'French', createdAt: now() },
    ],
    companies: [
      { companyId: 1, companyName: 'McKinsey & Company', ctypeId: 1, createdAt: now() },
      { companyId: 2, companyName: 'Google', ctypeId: 2, createdAt: now() },
      { companyId: 3, companyName: 'Goldman Sachs', ctypeId: 3, createdAt: now() },
    ],
    jobCategories: [
      { jobCatId: 1, categoryName: 'Strategy Consultant', createdAt: now() },
      { jobCatId: 2, categoryName: 'Product Manager', createdAt: now() },
      { jobCatId: 3, categoryName: 'Investment Banking Analyst', createdAt: now() },
    ],
    applications: [
      {
        applicationId: 1,
        companyId: 1,
        jobName: 'Associate Consultant',
        langId: 1,
        status: 'open',
        jobCatId: 1,
        createdAt: now(),
      },
      {
        applicationId: 2,
        companyId: 2,
        jobName: 'Senior PM',
        langId: 1,
        status: 'open',
        jobCatId: 2,
        createdAt: now(),
      },
    ],
    trackers: [
      {
        applicationId: 1,
        contactName: 'Jane Recruiter',
        contactEmail: 'jane@mckinsey.com',
        positionUrl: 'https://example.com/jobs/associate',
      },
      {
        applicationId: 2,
        contactName: null,
        contactEmail: null,
        positionUrl: null,
      },
    ],
    resumeDetails: [
      {
        applicationId: 1,
        ed1: 'MBA, INSEAD',
        ed2: 'BSc Economics, ITAM',
        ed3: null,
        ex1: 'Strategy lead at regional firm',
        ex2: null,
        ex3: null,
        skills: 'Strategy, Excel, Python',
        interests: 'Travel, chess',
        fileId: null,
      },
      {
        applicationId: 2,
        ed1: null,
        ed2: null,
        ed3: null,
        ex1: null,
        ex2: null,
        ex3: null,
        skills: null,
        interests: null,
        fileId: null,
      },
    ],
    coverLetters: [
      {
        applicationId: 1,
        header: 'Dear Hiring Team,',
        body: 'I am excited to apply for the Associate Consultant role...',
        close: 'Sincerely,',
        fileId: null,
      },
      {
        applicationId: 2,
        header: null,
        body: null,
        close: null,
        fileId: null,
      },
    ],
    websites: [
      { siteId: 1, address: 'https://www.linkedin.com', createdAt: now(), lastModification: null },
      { siteId: 2, address: 'https://www.glassdoor.com', createdAt: now(), lastModification: null },
    ],
    generationLogs: [],
    nextIds: {
      ctypeId: 4,
      langId: 4,
      companyId: 4,
      jobCatId: 4,
      applicationId: 3,
      siteId: 3,
      pdfId: 1,
    },
  }
}

let store = createInitialStore()

function nextId(key: keyof MockStore['nextIds']): number {
  const id = store.nextIds[key]
  store.nextIds[key] = id + 1
  return id
}

function delay(ms = 180) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function existsIgnoreCase(values: string[], candidate: string) {
  const normalized = candidate.trim().toLowerCase()
  return values.some((value) => value.trim().toLowerCase() === normalized)
}

function hydrateCompany(company: Company): Company {
  const industry = store.companyTypes.find((type) => type.ctypeId === company.ctypeId)?.typeName
  return { ...company, industry }
}

function hydrateApplication(app: Application): ApplicationWithDetails {
  const company = store.companies.find((item) => item.companyId === app.companyId)
  const language = store.languages.find((item) => item.langId === app.langId)?.language ?? null
  const categoryName =
    store.jobCategories.find((item) => item.jobCatId === app.jobCatId)?.categoryName ?? null

  return {
    ...app,
    companyName: company?.companyName ?? 'Unknown',
    language,
    categoryName,
  }
}

function hydrateTracker(tracker: TrackerDetails): TrackerWithDetails {
  const app = store.applications.find((item) => item.applicationId === tracker.applicationId)
  if (!app) {
    throw new ApiClientError('Application not found for tracker row.', 404)
  }
  const hydrated = hydrateApplication(app)
  return {
    ...tracker,
    jobName: hydrated.jobName,
    companyName: hydrated.companyName,
    language: hydrated.language,
    status: hydrated.status,
    categoryName: hydrated.categoryName,
    createdAt: hydrated.createdAt,
  }
}

function provisionApplicationChildren(applicationId: number) {
  store.trackers.push({
    applicationId,
    contactName: null,
    contactEmail: null,
    positionUrl: null,
  })
  store.resumeDetails.push({
    applicationId,
    ed1: null,
    ed2: null,
    ed3: null,
    ex1: null,
    ex2: null,
    ex3: null,
    skills: null,
    interests: null,
    fileId: null,
  })
  store.coverLetters.push({
    applicationId,
    header: null,
    body: null,
    close: null,
    fileId: null,
  })
}

export const mockDb = {
  async reset() {
    await delay(80)
    store = createInitialStore()
  },

  async listCompanyTypes(): Promise<CompanyType[]> {
    await delay()
    return [...store.companyTypes].sort((a, b) => a.typeName.localeCompare(b.typeName))
  },

  async createCompanyType(typeName: string): Promise<CompanyType> {
    await delay()
    if (existsIgnoreCase(store.companyTypes.map((item) => item.typeName), typeName)) {
      throw new ApiClientError(`'${typeName}' already exists.`, 409, 'DUPLICATE')
    }
    const record: CompanyType = { ctypeId: nextId('ctypeId'), typeName: typeName.trim(), createdAt: now() }
    store.companyTypes.push(record)
    return record
  },

  async listLanguages(): Promise<Language[]> {
    await delay()
    return [...store.languages].sort((a, b) => a.language.localeCompare(b.language))
  },

  async createLanguage(language: string): Promise<Language> {
    await delay()
    if (existsIgnoreCase(store.languages.map((item) => item.language), language)) {
      throw new ApiClientError(`'${language}' already exists.`, 409, 'DUPLICATE')
    }
    const record: Language = { langId: nextId('langId'), language: language.trim(), createdAt: now() }
    store.languages.push(record)
    return record
  },

  async getOrCreateLanguage(name: string): Promise<Language> {
    await delay(60)
    const existing = store.languages.find(
      (item) => item.language.toLowerCase() === name.trim().toLowerCase(),
    )
    if (existing) return existing
    return this.createLanguage(name)
  },

  async listCompanies(): Promise<Company[]> {
    await delay()
    return [...store.companies]
      .map(hydrateCompany)
      .sort((a, b) => a.companyName.localeCompare(b.companyName))
  },

  async createCompany(companyName: string, ctypeId: number): Promise<Company> {
    await delay()
    if (existsIgnoreCase(store.companies.map((item) => item.companyName), companyName)) {
      throw new ApiClientError(`'${companyName}' already exists.`, 409, 'DUPLICATE')
    }
    const record: Company = {
      companyId: nextId('companyId'),
      companyName: companyName.trim(),
      ctypeId,
      createdAt: now(),
    }
    store.companies.push(record)
    return hydrateCompany(record)
  },

  async listJobCategories(): Promise<JobCategory[]> {
    await delay()
    return [...store.jobCategories].sort((a, b) => a.categoryName.localeCompare(b.categoryName))
  },

  async getOrCreateJobCategory(name: string): Promise<JobCategory> {
    await delay(60)
    const existing = store.jobCategories.find(
      (item) => item.categoryName.toLowerCase() === name.trim().toLowerCase(),
    )
    if (existing) return existing
    const record: JobCategory = {
      jobCatId: nextId('jobCatId'),
      categoryName: name.trim(),
      createdAt: now(),
    }
    store.jobCategories.push(record)
    return record
  },

  async listApplications(): Promise<ApplicationWithDetails[]> {
    await delay()
    return [...store.applications]
      .map(hydrateApplication)
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  },

  async createApplication(payload: CreateApplicationPayload): Promise<ApplicationWithDetails> {
    await delay()
    const record: Application = {
      applicationId: nextId('applicationId'),
      ...payload,
      createdAt: now(),
    }
    store.applications.push(record)
    provisionApplicationChildren(record.applicationId)
    return hydrateApplication(record)
  },

  async updateApplication(payload: UpdateApplicationPayload): Promise<ApplicationWithDetails> {
    await delay()
    const index = store.applications.findIndex((item) => item.applicationId === payload.applicationId)
    if (index === -1) {
      throw new ApiClientError('Application not found.', 404)
    }
    const updated: Application = {
      applicationId: payload.applicationId,
      companyId: payload.companyId,
      jobName: payload.jobName,
      langId: payload.langId,
      status: payload.status,
      jobCatId: payload.jobCatId,
      createdAt: store.applications[index].createdAt,
    }
    store.applications[index] = updated
    return hydrateApplication(updated)
  },

  async listTrackers(): Promise<TrackerWithDetails[]> {
    await delay()
    return [...store.trackers]
      .map(hydrateTracker)
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  },

  async updateTracker(payload: UpdateTrackerPayload): Promise<TrackerWithDetails> {
    await delay()
    const index = store.trackers.findIndex((item) => item.applicationId === payload.applicationId)
    if (index === -1) {
      throw new ApiClientError('Tracking record not found.', 404)
    }
    const updated: TrackerDetails = {
      applicationId: payload.applicationId,
      contactName: payload.contactName?.trim() || null,
      contactEmail: payload.contactEmail?.trim() || null,
      positionUrl: payload.positionUrl?.trim() || null,
    }
    store.trackers[index] = updated
    return hydrateTracker(updated)
  },

  async listWebsites(): Promise<Website[]> {
    await delay()
    return [...store.websites].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  },
}

export type MockDb = typeof mockDb
