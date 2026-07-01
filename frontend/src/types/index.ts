export type ApplicationStatus = 'open' | 'closed'
export type FileType = 'cv' | 'cover letter'

export interface CompanyType {
  ctypeId: number
  typeName: string
  createdAt: string
}

export interface Language {
  langId: number
  language: string
  createdAt: string
}

export interface Company {
  companyId: number
  companyName: string
  ctypeId: number | null
  industry?: string
  createdAt: string
}

export interface JobCategory {
  jobCatId: number
  categoryName: string
  createdAt: string
}

export interface Application {
  applicationId: number
  companyId: number
  jobName: string
  langId: number | null
  status: ApplicationStatus
  jobCatId: number | null
  createdAt: string
}

export interface ApplicationWithDetails extends Application {
  companyName: string
  language: string | null
  categoryName: string | null
}

export interface TrackerDetails {
  applicationId: number
  contactName: string | null
  contactEmail: string | null
  positionUrl: string | null
}

export interface TrackerWithDetails extends TrackerDetails {
  jobName: string
  companyName: string
  language: string | null
  status: ApplicationStatus
  categoryName: string | null
  createdAt: string
}

export interface UpdateTrackerPayload {
  applicationId: number
  contactName: string | null
  contactEmail: string | null
  positionUrl: string | null
}

export interface ResumeDetails {
  applicationId: number
  ed1: string | null
  ed2: string | null
  ed3: string | null
  ex1: string | null
  ex2: string | null
  ex3: string | null
  skills: string | null
  interests: string | null
  fileId: number | null
}

export interface ResumeDetailsRow extends ResumeDetails {
  companyName: string
  jobName: string
  language: string | null
  status: ApplicationStatus
  categoryName: string | null
  fileName: string | null
  createdAt: string
}

export interface UpdateResumeDetailsPayload {
  applicationId: number
  ed1?: string | null
  ed2?: string | null
  ed3?: string | null
  ex1?: string | null
  ex2?: string | null
  ex3?: string | null
  skills?: string | null
  interests?: string | null
  fileId?: number | null
}

export interface CoverLetter {
  applicationId: number
  header: string | null
  body: string | null
  close: string | null
  fileId: number | null
}

export interface CoverLetterRow extends CoverLetter {
  companyName: string
  jobName: string
  language: string | null
  status: ApplicationStatus
  categoryName: string | null
  fileName: string | null
  createdAt: string
}

export interface UpdateCoverLetterPayload {
  applicationId: number
  header?: string | null
  body?: string | null
  close?: string | null
  fileId?: number | null
}

export interface FileTemplate {
  fileId: number
  fileName: string
  fileHash: string
  fileType: FileType
  langId: number | null
  language?: string | null
  activeStatus: boolean
  createdAt: string
}

export interface GenerationLog {
  pdfId: number
  applicationId: number
  fileHash: string
  fileName: string | null
  outputFile: string
  pdfSuccess: boolean
  createdAt: string
}

export type DocumentCategory = 'Resume' | 'Cover Letter'

export interface GenerationOption {
  applicationId: number
  category: DocumentCategory
  companyName: string
  jobName: string
  language: string | null
  status: ApplicationStatus
  categoryName: string | null
  fileName: string | null
  fileHash: string | null
  fileType: FileType | null
  createdAt: string
}

export interface GenerateDocumentPayload {
  applicationId: number
  category: DocumentCategory
  prefix?: string | null
}

export interface GenerateDocumentResult {
  pdfId: number
  outputFile: string
  pdfSuccess: boolean
  downloadUrl: string | null
}

export interface DownloadUrlResult {
  downloadUrl: string
  fileName: string
}

export interface UpdateTemplatePayload {
  fileId: number
  fileType?: FileType
  langId?: number | null
}

export interface Website {
  siteId: number
  address: string
  createdAt: string
  lastModification: string | null
}

export interface CreateApplicationPayload {
  companyId: number
  jobName: string
  langId: number | null
  status: ApplicationStatus
  jobCatId: number | null
}

export interface UpdateApplicationPayload extends CreateApplicationPayload {
  applicationId: number
}

export interface MilestoneProgress {
  m1: boolean
  m2: boolean
  m3: boolean
  m4: boolean
  m5: boolean
}

export interface ApiError {
  message: string
  code?: string
}

export interface AnalyticsMetrics {
  totalApplications: number
  readyResumes: number
  readyCoverLetters: number
  cvPrepRate: number
}

export interface MonthlyActivity {
  yearMonth: string
  apps: number
  resumes: number
  coverLetters: number
}

export interface LabelCount {
  name: string
  count: number
}

export interface AnalyticsSummary {
  metrics: AnalyticsMetrics
  monthlyActivity: MonthlyActivity[]
  statusDistribution: LabelCount[]
  languageDistribution: LabelCount[]
  categoryDistribution: LabelCount[]
  industryDistribution: LabelCount[]
}
