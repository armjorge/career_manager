import { useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { ApiClientError } from '@/api/client'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { DataTable } from '@/components/data/DataTable'
import { MilestoneStepper } from '@/components/pipeline/MilestoneStepper'
import { Field, Label } from '@/components/ui/Label'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import {
  useApplications,
  useCreateApplication,
  useJobCategories,
  useResolveCategory,
  useResolveLanguage,
  useUpdateApplication,
} from '@/hooks/useApplications'
import { useCompanies, useLanguages } from '@/hooks/useCompanies'
import { useUiStore } from '@/stores/uiStore'
import { applicationSchema, type ApplicationFormValues } from '@/validators/schemas'
import type { ApplicationWithDetails } from '@/types'

const ADD_NEW = '__add_new__'

function applicationLabel(app: ApplicationWithDetails) {
  return `${app.jobName} | ${app.companyName} | ${new Date(app.createdAt).toLocaleDateString()}`
}

function Milestone1Form() {
  const { data: applications = [], isLoading } = useApplications()
  const { data: companies = [] } = useCompanies()
  const { data: languages = [] } = useLanguages()
  const { data: categories = [] } = useJobCategories()
  const createApplication = useCreateApplication()
  const updateApplication = useUpdateApplication()
  const resolveLanguage = useResolveLanguage()
  const resolveCategory = useResolveCategory()
  const { selectedApplicationId, setSelectedApplicationId } = useUiStore()

  const [feedback, setFeedback] = useState<{ variant: 'success' | 'error'; message: string } | null>(null)
  const [languageMode, setLanguageMode] = useState<string>('')
  const [categoryMode, setCategoryMode] = useState<string>('')

  const selectedApp = useMemo(
    () => applications.find((app) => app.applicationId === selectedApplicationId) ?? null,
    [applications, selectedApplicationId],
  )

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<ApplicationFormValues>({
    resolver: zodResolver(applicationSchema),
    defaultValues: {
      companyId: undefined,
      jobName: '',
      status: 'open',
      langId: null,
      jobCatId: null,
      newLanguage: '',
      newCategory: '',
    },
  })

  useEffect(() => {
    if (!selectedApp) {
      reset({
        companyId: companies[0]?.companyId,
        jobName: '',
        status: 'open',
        langId: languages[0]?.langId ?? null,
        jobCatId: categories[0]?.jobCatId ?? null,
        newLanguage: '',
        newCategory: '',
      })
      setLanguageMode(languages[0]?.langId?.toString() ?? ADD_NEW)
      setCategoryMode(categories[0]?.jobCatId?.toString() ?? ADD_NEW)
      return
    }

    const langMatch = languages.find((item) => item.langId === selectedApp.langId)
    const catMatch = categories.find((item) => item.jobCatId === selectedApp.jobCatId)

    reset({
      companyId: selectedApp.companyId,
      jobName: selectedApp.jobName,
      status: selectedApp.status,
      langId: selectedApp.langId,
      jobCatId: selectedApp.jobCatId,
      newLanguage: '',
      newCategory: '',
    })
    setLanguageMode(langMatch ? String(langMatch.langId) : ADD_NEW)
    setCategoryMode(catMatch ? String(catMatch.jobCatId) : ADD_NEW)
  }, [selectedApp, companies, languages, categories, reset])

  const onSubmitCreate = handleSubmit(async (values) => {
    setFeedback(null)
    try {
      let langId = values.langId
      let jobCatId = values.jobCatId

      if (languageMode === ADD_NEW) {
        if (!values.newLanguage?.trim()) {
          setFeedback({ variant: 'error', message: 'Enter a new language or select an existing one.' })
          return
        }
        const created = await resolveLanguage.mutateAsync(values.newLanguage.trim())
        langId = created.langId
      } else if (languageMode) {
        langId = Number(languageMode)
      }

      if (categoryMode === ADD_NEW) {
        if (!values.newCategory?.trim()) {
          setFeedback({ variant: 'error', message: 'Enter a new category or select an existing one.' })
          return
        }
        const created = await resolveCategory.mutateAsync(values.newCategory.trim())
        jobCatId = created.jobCatId
      } else if (categoryMode) {
        jobCatId = Number(categoryMode)
      }

      const created = await createApplication.mutateAsync({
        companyId: values.companyId,
        jobName: values.jobName.trim(),
        status: values.status,
        langId,
        jobCatId,
      })

      setSelectedApplicationId(created.applicationId)
      setFeedback({ variant: 'success', message: 'Application created successfully.' })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Could not create application.'
      setFeedback({ variant: 'error', message })
    }
  })

  const onSubmitUpdate = handleSubmit(async (values) => {
    if (!selectedApplicationId) {
      setFeedback({ variant: 'error', message: 'Select an application to update.' })
      return
    }

    setFeedback(null)
    try {
      let langId = values.langId
      let jobCatId = values.jobCatId

      if (languageMode === ADD_NEW) {
        if (!values.newLanguage?.trim()) {
          setFeedback({ variant: 'error', message: 'Enter a new language or select an existing one.' })
          return
        }
        const created = await resolveLanguage.mutateAsync(values.newLanguage.trim())
        langId = created.langId
      } else if (languageMode) {
        langId = Number(languageMode)
      }

      if (categoryMode === ADD_NEW) {
        if (!values.newCategory?.trim()) {
          setFeedback({ variant: 'error', message: 'Enter a new category or select an existing one.' })
          return
        }
        const created = await resolveCategory.mutateAsync(values.newCategory.trim())
        jobCatId = created.jobCatId
      } else if (categoryMode) {
        jobCatId = Number(categoryMode)
      }

      await updateApplication.mutateAsync({
        applicationId: selectedApplicationId,
        companyId: values.companyId,
        jobName: values.jobName.trim(),
        status: values.status,
        langId,
        jobCatId,
      })

      setFeedback({ variant: 'success', message: 'Application updated successfully.' })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Could not update application.'
      setFeedback({ variant: 'error', message })
    }
  })

  const isSaving =
    createApplication.isPending ||
    updateApplication.isPending ||
    resolveLanguage.isPending ||
    resolveCategory.isPending

  return (
    <div className="space-y-6">
      <DataTable
        isLoading={isLoading}
        data={applications}
        emptyMessage="No applications found. Create your first one below."
        columns={[
          { key: 'jobName', header: 'Position' },
          { key: 'companyName', header: 'Company' },
          { key: 'language', header: 'Language', render: (row) => row.language ?? '—' },
          { key: 'status', header: 'Status' },
          { key: 'categoryName', header: 'Category', render: (row) => row.categoryName ?? '—' },
          {
            key: 'createdAt',
            header: 'Created',
            render: (row) => new Date(row.createdAt).toLocaleDateString(),
          },
        ]}
      />

      <Card>
        <CardHeader>
          <CardTitle>Add or Edit Application</CardTitle>
          <CardDescription>
            Milestone 1 — core application metadata. Select an existing row to edit, or leave blank
            to create a new one.
          </CardDescription>
        </CardHeader>

        <div className="mb-5">
          <Field>
            <Label htmlFor="edit-select">Existing application (optional)</Label>
            <Select
              id="edit-select"
              value={selectedApplicationId ?? ''}
              onChange={(event) => {
                const value = event.target.value
                setSelectedApplicationId(value ? Number(value) : null)
              }}
            >
              <option value="">Create new application</option>
              {applications.map((app) => (
                <option key={app.applicationId} value={app.applicationId}>
                  {applicationLabel(app)}
                </option>
              ))}
            </Select>
          </Field>
        </div>

        <form className="grid gap-5 md:grid-cols-2">
          <Field>
            <Label htmlFor="companyId">Company</Label>
            <Select
              id="companyId"
              {...register('companyId', { valueAsNumber: true })}
              error={errors.companyId?.message}
            >
              {companies.map((company) => (
                <option key={company.companyId} value={company.companyId}>
                  {company.companyName}
                </option>
              ))}
            </Select>
          </Field>

          <Field>
            <Label htmlFor="jobName">Job position</Label>
            <Input
              id="jobName"
              placeholder="e.g. Associate Consultant"
              {...register('jobName')}
              error={errors.jobName?.message}
            />
          </Field>

          <Field>
            <Label htmlFor="status">Status</Label>
            <Select id="status" {...register('status')}>
              <option value="open">open</option>
              <option value="closed">closed</option>
            </Select>
          </Field>

          <Field>
            <Label htmlFor="languageMode">Language</Label>
            <Select
              id="languageMode"
              value={languageMode}
              onChange={(event) => {
                setLanguageMode(event.target.value)
                if (event.target.value !== ADD_NEW) {
                  setValue('langId', Number(event.target.value))
                }
              }}
            >
              <option value={ADD_NEW}>Add new...</option>
              {languages.map((language) => (
                <option key={language.langId} value={language.langId}>
                  {language.language}
                </option>
              ))}
            </Select>
          </Field>

          {languageMode === ADD_NEW ? (
            <Field className="md:col-span-2">
              <Label htmlFor="newLanguage">New language</Label>
              <Input id="newLanguage" placeholder="e.g. Portuguese" {...register('newLanguage')} />
            </Field>
          ) : null}

          <Field>
            <Label htmlFor="categoryMode">Job category</Label>
            <Select
              id="categoryMode"
              value={categoryMode}
              onChange={(event) => {
                setCategoryMode(event.target.value)
                if (event.target.value !== ADD_NEW) {
                  setValue('jobCatId', Number(event.target.value))
                }
              }}
            >
              <option value={ADD_NEW}>Add new...</option>
              {categories.map((category) => (
                <option key={category.jobCatId} value={category.jobCatId}>
                  {category.categoryName}
                </option>
              ))}
            </Select>
          </Field>

          {categoryMode === ADD_NEW ? (
            <Field className="md:col-span-2">
              <Label htmlFor="newCategory">New category</Label>
              <Input id="newCategory" placeholder="e.g. Data Analyst" {...register('newCategory')} />
            </Field>
          ) : null}

          {feedback ? (
            <div className="md:col-span-2">
              <Alert variant={feedback.variant} message={feedback.message} />
            </div>
          ) : null}

          <div className="flex flex-wrap gap-3 md:col-span-2">
            <Button type="button" disabled={isSaving || !selectedApplicationId} onClick={onSubmitUpdate}>
              {updateApplication.isPending ? 'Saving...' : 'Save Changes (Milestone 1)'}
            </Button>
            <Button type="button" variant="secondary" disabled={isSaving} onClick={onSubmitCreate}>
              {createApplication.isPending ? 'Creating...' : 'Create New Application'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

function Milestone2Placeholder() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Tracking Details (Milestone 2)</CardTitle>
        <CardDescription>
          Contact name, email, and position URL editing will land in Sprint 2. The mock API already
          provisions tracker rows when applications are created.
        </CardDescription>
      </CardHeader>
      <Alert
        variant="info"
        message="Select an application in Milestone 1, then continue here once the tracking form is wired."
      />
    </Card>
  )
}

export function ApplicationsPage() {
  const [activeTab, setActiveTab] = useState<'m1' | 'm2'>('m1')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Applications & Tracking</h1>
        <p className="mt-2 text-muted">
          Manage your application pipeline across milestones — from first submission to document
          readiness.
        </p>
      </div>

      <MilestoneStepper
        active={activeTab === 'm1' ? 'm1' : 'm2'}
        completed={{ m1: true, m2: false, m3: false, m4: false, m5: false }}
      />

      <div className="flex gap-2 border-b border-border">
        <button
          type="button"
          onClick={() => setActiveTab('m1')}
          className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'm1'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted hover:text-foreground'
          }`}
        >
          Milestone 1: Applications
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('m2')}
          className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'm2'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted hover:text-foreground'
          }`}
        >
          Milestone 2: Tracking
        </button>
      </div>

      {activeTab === 'm1' ? <Milestone1Form /> : <Milestone2Placeholder />}
    </div>
  )
}
