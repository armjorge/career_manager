import { z } from 'zod'

export const companyTypeSchema = z.object({
  typeName: z.string().trim().min(1, 'Type name is required'),
})

export const languageSchema = z.object({
  language: z.string().trim().min(1, 'Language is required'),
})

export const companySchema = z.object({
  companyName: z.string().trim().min(1, 'Company name is required'),
  ctypeId: z.number({ error: 'Industry type is required' }).int().positive('Industry type is required'),
})

export const applicationSchema = z.object({
  companyId: z.number({ error: 'Company is required' }).int().positive('Company is required'),
  jobName: z.string().trim().min(1, 'Job position is required'),
  status: z.enum(['open', 'closed']),
  langId: z.number().int().positive().nullable(),
  jobCatId: z.number().int().positive().nullable(),
  newLanguage: z.string().optional(),
  newCategory: z.string().optional(),
})

export type CompanyTypeFormValues = z.infer<typeof companyTypeSchema>
export type LanguageFormValues = z.infer<typeof languageSchema>
export type CompanyFormValues = z.infer<typeof companySchema>
export type ApplicationFormValues = z.infer<typeof applicationSchema>
