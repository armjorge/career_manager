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
  siteId: z.number().int().positive().nullable(),
  newLanguage: z.string().optional(),
  newCategory: z.string().optional(),
})

export const trackerSchema = z.object({
  contactName: z.string().optional(),
  contactEmail: z
    .string()
    .trim()
    .refine((value) => value === '' || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value), {
      message: 'Enter a valid email address',
    }),
  positionUrl: z
    .string()
    .trim()
    .refine((value) => {
      if (!value) return true
      try {
        new URL(value)
        return true
      } catch {
        return false
      }
    }, { message: 'Enter a valid URL' }),
})

export const signInSchema = z.object({
  email: z.string().trim().email('Enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

export const signUpSchema = signInSchema.extend({
  name: z.string().trim().min(1, 'Name is required'),
})

export type SignInFormValues = z.infer<typeof signInSchema>
export type SignUpFormValues = z.infer<typeof signUpSchema>

export type CompanyTypeFormValues = z.infer<typeof companyTypeSchema>
export type LanguageFormValues = z.infer<typeof languageSchema>
export type CompanyFormValues = z.infer<typeof companySchema>
export type ApplicationFormValues = z.infer<typeof applicationSchema>
export type TrackerFormValues = z.infer<typeof trackerSchema>
