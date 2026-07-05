import type {
  AnalyticsSummary,
  Application,
  ApplicationWithDetails,
  Company,
  CompanyType,
  CoverLetter,
  CreateApplicationPayload,
  DocumentCategory,
  FileTemplate,
  GenerateDocumentPayload,
  GenerateDocumentResult,
  GenerationLog,
  GenerationOption,
  JobCategory,
  Language,
  ResumeDetails,
  ResumeDetailsRow,
  CoverLetterRow,
  UpdateCoverLetterPayload,
  UpdateResumeDetailsPayload,
  UpdateTemplatePayload,
  DownloadUrlResult,
  TrackerDetails,
  TrackerWithDetails,
  UpdateApplicationPayload,
  UpdateTrackerPayload,
  Website,
  LabelCount,
  MonthlyActivity,
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
  templates: FileTemplate[]
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
        siteId: null,
        createdAt: now(),
      },
      {
        applicationId: 2,
        companyId: 2,
        jobName: 'Senior PM',
        langId: 1,
        status: 'open',
        jobCatId: 2,
        siteId: null,
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
    templates: [
      {
        fileId: 1,
        fileName: 'Curriculum_English.docx',
        fileHash: 'abc123mockhash0000000000000001',
        fileType: 'cv',
        langId: 1,
        language: 'English',
        activeStatus: true,
        createdAt: now(),
      },
      {
        fileId: 2,
        fileName: 'Cover_letter_English.docx',
        fileHash: 'abc123mockhash0000000000000002',
        fileType: 'cover letter',
        langId: 1,
        language: 'English',
        activeStatus: true,
        createdAt: now(),
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
      fileId: 3,
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
    siteAddress: null,
  }
}

function hydrateResumeRow(details: ResumeDetails): ResumeDetailsRow {
  const app = store.applications.find((item) => item.applicationId === details.applicationId)
  if (!app) {
    throw new ApiClientError('Application not found for resume row.', 404)
  }
  const hydrated = hydrateApplication(app)
  const template = store.templates.find((item) => item.fileId === details.fileId)
  return {
    ...details,
    companyName: hydrated.companyName,
    jobName: hydrated.jobName,
    language: hydrated.language,
    status: hydrated.status,
    categoryName: hydrated.categoryName,
    fileName: template?.fileName ?? null,
    createdAt: hydrated.createdAt,
  }
}

function hydrateCoverLetterRow(letter: CoverLetter): CoverLetterRow {
  const app = store.applications.find((item) => item.applicationId === letter.applicationId)
  if (!app) {
    throw new ApiClientError('Application not found for cover letter row.', 404)
  }
  const hydrated = hydrateApplication(app)
  const template = store.templates.find((item) => item.fileId === letter.fileId)
  return {
    ...letter,
    companyName: hydrated.companyName,
    jobName: hydrated.jobName,
    language: hydrated.language,
    status: hydrated.status,
    categoryName: hydrated.categoryName,
    fileName: template?.fileName ?? null,
    createdAt: hydrated.createdAt,
  }
}

function proposeOutputFilename(
  prefix: string | null | undefined,
  companyName: string,
  categoryName: string | null,
  category: DocumentCategory,
) {
  const catSuffix = category === 'Resume' ? 'CV' : 'CLetter'
  const role = categoryName ?? catSuffix
  const parts = [prefix?.trim(), companyName, role].filter(Boolean)
  return `${parts.join(' ')}.docx`
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

function yearMonth(iso: string): string {
  const date = new Date(iso)
  const month = String(date.getUTCMonth() + 1).padStart(2, '0')
  return `${date.getUTCFullYear()}-${month}`
}

function countBy<T>(items: T[], getKey: (item: T) => string): LabelCount[] {
  const totals = new Map<string, number>()
  for (const item of items) {
    const key = getKey(item)
    totals.set(key, (totals.get(key) ?? 0) + 1)
  }
  return [...totals.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
}

function buildMonthlyActivity(): MonthlyActivity[] {
  const months = new Map<string, MonthlyActivity>()

  const ensureMonth = (month: string) => {
    if (!months.has(month)) {
      months.set(month, { yearMonth: month, apps: 0, resumes: 0, coverLetters: 0 })
    }
    return months.get(month)!
  }

  for (const app of store.applications) {
    const month = yearMonth(app.createdAt)
    ensureMonth(month).apps += 1
  }

  for (const resume of store.resumeDetails) {
    if (!resume.fileId) continue
    const app = store.applications.find((item) => item.applicationId === resume.applicationId)
    if (!app) continue
    ensureMonth(yearMonth(app.createdAt)).resumes += 1
  }

  for (const letter of store.coverLetters) {
    if (!letter.fileId) continue
    const app = store.applications.find((item) => item.applicationId === letter.applicationId)
    if (!app) continue
    ensureMonth(yearMonth(app.createdAt)).coverLetters += 1
  }

  return [...months.values()].sort((a, b) => a.yearMonth.localeCompare(b.yearMonth))
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
      siteId: payload.siteId,
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

  async listWebsites(): Promise<(Website & { applicationCount: number })[]> {
    await delay()
    return [...store.websites]
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
      .map((site) => ({
        ...site,
        applicationCount: store.applications.filter((app) => app.siteId === site.siteId).length,
      }))
  },

  async createWebsite(address: string): Promise<Website & { applicationCount: number }> {
    await delay()
    const normalized = address.trim().toLowerCase()
    if (store.websites.some((site) => site.address.trim().toLowerCase() === normalized)) {
      throw new ApiClientError(`'${address.trim()}' already exists.`, 409, 'DUPLICATE')
    }
    const record: Website = {
      siteId: nextId('siteId'),
      address: address.trim(),
      createdAt: now(),
      lastModification: null,
    }
    store.websites.push(record)
    return { ...record, applicationCount: 0 }
  },

  async deleteWebsite(siteId: number): Promise<void> {
    await delay()
    const index = store.websites.findIndex((site) => site.siteId === siteId)
    if (index === -1) {
      throw new ApiClientError('Site not found.', 404, 'NOT_FOUND')
    }
    const inUse = store.applications.some((app) => app.siteId === siteId)
    if (inUse) {
      throw new ApiClientError('Cannot delete — linked to active applications.', 409, 'IN_USE')
    }
    store.websites.splice(index, 1)
  },

  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    await delay()
    const monthlyActivity = buildMonthlyActivity()
    const totalApplications = monthlyActivity.reduce((sum, row) => sum + row.apps, 0)
    const readyResumes = monthlyActivity.reduce((sum, row) => sum + row.resumes, 0)
    const readyCoverLetters = monthlyActivity.reduce((sum, row) => sum + row.coverLetters, 0)
    const cvPrepRate =
      totalApplications > 0 ? Math.round((readyResumes / totalApplications) * 1000) / 10 : 0

    const applications = store.applications.map(hydrateApplication)

    return {
      metrics: {
        totalApplications,
        readyResumes,
        readyCoverLetters,
        cvPrepRate,
      },
      monthlyActivity,
      statusDistribution: countBy(applications, (app) => app.status),
      languageDistribution: countBy(
        applications.filter((app) => app.language),
        (app) => app.language ?? 'Unknown',
      ),
      categoryDistribution: countBy(
        applications,
        (app) => app.categoryName ?? 'Uncategorized',
      ),
      industryDistribution: countBy(applications, (app) => {
        const company = store.companies.find((item) => item.companyId === app.companyId)
        const industry = store.companyTypes.find((item) => item.ctypeId === company?.ctypeId)
        return industry?.typeName ?? 'Other/Unknown'
      }),
    }
  },

  async listResumeRows(): Promise<ResumeDetailsRow[]> {
    await delay()
    return store.resumeDetails.map(hydrateResumeRow)
  },

  async updateResumeDetails(payload: UpdateResumeDetailsPayload): Promise<ResumeDetailsRow> {
    await delay()
    const index = store.resumeDetails.findIndex((item) => item.applicationId === payload.applicationId)
    if (index === -1) {
      throw new ApiClientError('Resume details not found.', 404)
    }
    const updated: ResumeDetails = {
      ...store.resumeDetails[index],
      ed1: payload.ed1 ?? store.resumeDetails[index].ed1,
      ed2: payload.ed2 ?? store.resumeDetails[index].ed2,
      ed3: payload.ed3 ?? store.resumeDetails[index].ed3,
      ex1: payload.ex1 ?? store.resumeDetails[index].ex1,
      ex2: payload.ex2 ?? store.resumeDetails[index].ex2,
      ex3: payload.ex3 ?? store.resumeDetails[index].ex3,
      skills: payload.skills ?? store.resumeDetails[index].skills,
      interests: payload.interests ?? store.resumeDetails[index].interests,
      fileId: payload.fileId !== undefined ? payload.fileId : store.resumeDetails[index].fileId,
    }
    store.resumeDetails[index] = updated
    return hydrateResumeRow(updated)
  },

  async listCoverLetterRows(): Promise<CoverLetterRow[]> {
    await delay()
    return store.coverLetters.map(hydrateCoverLetterRow)
  },

  async updateCoverLetter(payload: UpdateCoverLetterPayload): Promise<CoverLetterRow> {
    await delay()
    const index = store.coverLetters.findIndex((item) => item.applicationId === payload.applicationId)
    if (index === -1) {
      throw new ApiClientError('Cover letter not found.', 404)
    }
    const updated: CoverLetter = {
      ...store.coverLetters[index],
      header: payload.header ?? store.coverLetters[index].header,
      body: payload.body ?? store.coverLetters[index].body,
      close: payload.close ?? store.coverLetters[index].close,
      fileId: payload.fileId !== undefined ? payload.fileId : store.coverLetters[index].fileId,
    }
    store.coverLetters[index] = updated
    return hydrateCoverLetterRow(updated)
  },

  async listTemplates(): Promise<FileTemplate[]> {
    await delay()
    return store.templates.filter((item) => item.activeStatus)
  },

  async uploadTemplate(file: File): Promise<FileTemplate> {
    await delay()
    const fileName = file.name
    const fileType = fileName.toLowerCase().includes('cover') ? 'cover letter' : 'cv'
    const record: FileTemplate = {
      fileId: nextId('fileId'),
      fileName,
      fileHash: `mockhash${Date.now()}`,
      fileType,
      langId: null,
      language: null,
      activeStatus: true,
      createdAt: now(),
    }
    store.templates.push(record)
    return record
  },

  async updateTemplate(payload: UpdateTemplatePayload): Promise<FileTemplate> {
    await delay()
    const index = store.templates.findIndex((item) => item.fileId === payload.fileId)
    if (index === -1) {
      throw new ApiClientError('Template not found.', 404)
    }
    const updated: FileTemplate = {
      ...store.templates[index],
      fileType: payload.fileType ?? store.templates[index].fileType,
      langId: payload.langId !== undefined ? payload.langId : store.templates[index].langId,
      language:
        payload.langId !== undefined
          ? store.languages.find((item) => item.langId === payload.langId)?.language ?? null
          : store.templates[index].language,
    }
    store.templates[index] = updated
    return updated
  },

  async deleteTemplate(fileId: number): Promise<void> {
    await delay()
    const index = store.templates.findIndex((item) => item.fileId === fileId)
    if (index === -1) {
      throw new ApiClientError('Template not found.', 404)
    }
    store.templates[index] = { ...store.templates[index], activeStatus: false }
  },

  async listGenerationOptions(): Promise<GenerationOption[]> {
    await delay()
    const options: GenerationOption[] = []

    for (const details of store.resumeDetails) {
      const template = store.templates.find(
        (item) => item.fileId === details.fileId && item.activeStatus,
      )
      if (!template) continue
      const row = hydrateResumeRow(details)
      options.push({
        applicationId: row.applicationId,
        category: 'Resume',
        companyName: row.companyName,
        jobName: row.jobName,
        language: row.language,
        status: row.status,
        categoryName: row.categoryName,
        fileName: template.fileName,
        fileHash: template.fileHash,
        fileType: template.fileType,
        createdAt: row.createdAt,
      })
    }

    for (const letter of store.coverLetters) {
      const template = store.templates.find(
        (item) => item.fileId === letter.fileId && item.activeStatus,
      )
      if (!template) continue
      const row = hydrateCoverLetterRow(letter)
      options.push({
        applicationId: row.applicationId,
        category: 'Cover Letter',
        companyName: row.companyName,
        jobName: row.jobName,
        language: row.language,
        status: row.status,
        categoryName: row.categoryName,
        fileName: template.fileName,
        fileHash: template.fileHash,
        fileType: template.fileType,
        createdAt: row.createdAt,
      })
    }

    return options.sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  },

  async generateDocument(payload: GenerateDocumentPayload): Promise<GenerateDocumentResult> {
    await delay(300)
    const options = await mockDb.listGenerationOptions()
    const match = options.find(
      (item) => item.applicationId === payload.applicationId && item.category === payload.category,
    )
    if (!match) {
      throw new ApiClientError('No active template linked for this application.', 400)
    }

    const baseName = proposeOutputFilename(
      payload.prefix,
      match.companyName,
      match.categoryName,
      payload.category,
    )
    const existing = new Set(store.generationLogs.map((item) => item.outputFile))
    let outputFile = baseName
    let counter = 1
    while (existing.has(outputFile)) {
      outputFile = baseName.replace('.docx', `_${counter}.docx`)
      counter += 1
    }

    const record: GenerationLog = {
      pdfId: nextId('pdfId'),
      applicationId: payload.applicationId,
      fileHash: match.fileHash ?? '',
      fileName: match.fileName,
      outputFile,
      pdfSuccess: true,
      createdAt: now(),
      companyName: match.companyName,
      jobName: match.jobName,
    }
    store.generationLogs.unshift(record)

    return {
      pdfId: record.pdfId,
      outputFile: record.outputFile,
      pdfSuccess: true,
      downloadUrl: null,
    }
  },

  async listGenerations(limit: number): Promise<GenerationLog[]> {
    await delay()
    return store.generationLogs.slice(0, limit)
  },

  async getDownloadUrl(pdfId: number): Promise<DownloadUrlResult> {
    await delay()
    const record = store.generationLogs.find((item) => item.pdfId === pdfId)
    if (!record || !record.pdfSuccess) {
      throw new ApiClientError('Generation record not available.', 404)
    }
    return {
      downloadUrl: '#',
      fileName: record.outputFile,
    }
  },

  async deleteGeneration(pdfId: number): Promise<void> {
    await delay()
    const index = store.generationLogs.findIndex((item) => item.pdfId === pdfId)
    if (index === -1) {
      throw new ApiClientError('Generation record not found.', 404)
    }
    store.generationLogs.splice(index, 1)
  },
}

export type MockDb = typeof mockDb
