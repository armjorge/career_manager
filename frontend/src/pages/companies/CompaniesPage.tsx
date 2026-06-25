import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { ApiClientError } from '@/api/client'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { DataTable } from '@/components/data/DataTable'
import { Field, Label } from '@/components/ui/Label'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import {
  useCompanies,
  useCompanyTypes,
  useCreateCompany,
  useCreateCompanyType,
  useCreateLanguage,
  useLanguages,
} from '@/hooks/useCompanies'
import {
  companySchema,
  companyTypeSchema,
  languageSchema,
  type CompanyFormValues,
  type CompanyTypeFormValues,
  type LanguageFormValues,
} from '@/validators/schemas'

function AddCompanyTypePanel() {
  const { data = [], isLoading } = useCompanyTypes()
  const createType = useCreateCompanyType()
  const [feedback, setFeedback] = useState<{ variant: 'success' | 'error'; message: string } | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CompanyTypeFormValues>({
    resolver: zodResolver(companyTypeSchema),
    defaultValues: { typeName: '' },
  })

  const onSubmit = handleSubmit(async (values) => {
    setFeedback(null)
    try {
      await createType.mutateAsync(values.typeName)
      reset()
      setFeedback({ variant: 'success', message: `'${values.typeName}' added successfully.` })
    } catch (error) {
      const message =
        error instanceof ApiClientError ? error.message : 'Could not add company type.'
      setFeedback({ variant: 'error', message })
    }
  })

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Company Types</CardTitle>
        <CardDescription>Industries and organization categories.</CardDescription>
      </CardHeader>

      <DataTable
        isLoading={isLoading}
        data={data}
        emptyMessage="No company types yet."
        columns={[{ key: 'typeName', header: 'Type Name' }]}
      />

      <form onSubmit={onSubmit} className="mt-4 space-y-3 border-t border-border pt-4">
        <Field>
          <Label htmlFor="typeName">Add new type</Label>
          <Input id="typeName" placeholder="e.g. Healthcare" {...register('typeName')} error={errors.typeName?.message} />
        </Field>
        {feedback ? <Alert variant={feedback.variant} message={feedback.message} /> : null}
        <Button type="submit" disabled={createType.isPending}>
          {createType.isPending ? 'Adding...' : 'Add Type'}
        </Button>
      </form>
    </Card>
  )
}

function AddLanguagePanel() {
  const { data = [], isLoading } = useLanguages()
  const createLanguage = useCreateLanguage()
  const [feedback, setFeedback] = useState<{ variant: 'success' | 'error'; message: string } | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<LanguageFormValues>({
    resolver: zodResolver(languageSchema),
    defaultValues: { language: '' },
  })

  const onSubmit = handleSubmit(async (values) => {
    setFeedback(null)
    try {
      await createLanguage.mutateAsync(values.language)
      reset()
      setFeedback({ variant: 'success', message: `'${values.language}' added successfully.` })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Could not add language.'
      setFeedback({ variant: 'error', message })
    }
  })

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Languages</CardTitle>
        <CardDescription>Languages used across applications and templates.</CardDescription>
      </CardHeader>

      <DataTable
        isLoading={isLoading}
        data={data}
        emptyMessage="No languages yet."
        columns={[{ key: 'language', header: 'Language' }]}
      />

      <form onSubmit={onSubmit} className="mt-4 space-y-3 border-t border-border pt-4">
        <Field>
          <Label htmlFor="language">Add new language</Label>
          <Input id="language" placeholder="e.g. German" {...register('language')} error={errors.language?.message} />
        </Field>
        {feedback ? <Alert variant={feedback.variant} message={feedback.message} /> : null}
        <Button type="submit" disabled={createLanguage.isPending}>
          {createLanguage.isPending ? 'Adding...' : 'Add Language'}
        </Button>
      </form>
    </Card>
  )
}

function AddCompanyPanel() {
  const { data: companies = [], isLoading } = useCompanies()
  const { data: types = [] } = useCompanyTypes()
  const createCompany = useCreateCompany()
  const [feedback, setFeedback] = useState<{ variant: 'success' | 'error'; message: string } | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CompanyFormValues>({
    resolver: zodResolver(companySchema),
    defaultValues: { companyName: '', ctypeId: undefined },
  })

  const onSubmit = handleSubmit(async (values) => {
    setFeedback(null)
    try {
      await createCompany.mutateAsync(values)
      reset()
      setFeedback({ variant: 'success', message: `'${values.companyName}' added successfully.` })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Could not add company.'
      setFeedback({ variant: 'error', message })
    }
  })

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Companies</CardTitle>
        <CardDescription>Target organizations linked to an industry type.</CardDescription>
      </CardHeader>

      <DataTable
        isLoading={isLoading}
        data={companies}
        emptyMessage="No companies yet."
        columns={[
          { key: 'companyName', header: 'Company' },
          { key: 'industry', header: 'Industry', render: (row) => row.industry ?? '—' },
        ]}
      />

      <form onSubmit={onSubmit} className="mt-4 space-y-3 border-t border-border pt-4">
        <Field>
          <Label htmlFor="companyName">Company name</Label>
          <Input
            id="companyName"
            placeholder="e.g. Bain & Company"
            {...register('companyName')}
            error={errors.companyName?.message}
          />
        </Field>
        <Field>
          <Label htmlFor="ctypeId">Industry / type</Label>
          <Select
            id="ctypeId"
            defaultValue=""
            {...register('ctypeId', { valueAsNumber: true })}
            error={errors.ctypeId?.message}
          >
            <option value="" disabled>
              Select industry
            </option>
            {types.map((type) => (
              <option key={type.ctypeId} value={type.ctypeId}>
                {type.typeName}
              </option>
            ))}
          </Select>
        </Field>
        {feedback ? <Alert variant={feedback.variant} message={feedback.message} /> : null}
        <Button type="submit" disabled={createCompany.isPending || types.length === 0}>
          {createCompany.isPending ? 'Adding...' : 'Add Company'}
        </Button>
      </form>
    </Card>
  )
}

export function CompaniesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Companies, Types & Languages</h1>
        <p className="mt-2 text-muted">
          Master data setup before creating applications. Changes are saved to your Neon Postgres
          workspace (scoped to your account).
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <AddCompanyTypePanel />
        <AddLanguagePanel />
        <AddCompanyPanel />
      </div>
    </div>
  )
}
