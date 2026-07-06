import { useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Plus } from 'lucide-react'
import { ApiClientError } from '@/api/client'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { DataTable } from '@/components/data/DataTable'
import { Field, Label } from '@/components/ui/Label'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import {
  useApplications,
  useCreateApplication,
  useJobCategories,
  useResolveCategory,
  useResolveLanguage,
  useTrackers,
  useUpdateApplication,
  useUpdateTracker,
} from '@/hooks/useApplications'
import { useCompanies, useLanguages } from '@/hooks/useCompanies'
import { useSites } from '@/hooks/useSites'
import { useUiStore } from '@/stores/uiStore'
import { applicationSchema, trackerSchema, type ApplicationFormValues, type TrackerFormValues } from '@/validators/schemas'
import type { ApplicationWithDetails, TrackerWithDetails } from '@/types'

const ADD_NEW = '__add_new__'

function applicationLabel(app: ApplicationWithDetails) {
  return `${app.jobName} | ${app.companyName} | ${new Date(app.createdAt).toLocaleDateString()}`
}

type AppFormMode = 'edit' | 'create'

function ApplicationForm({ mode, onCancel }: { mode: AppFormMode; onCancel?: () => void }) {
  const { data: applications = [] } = useApplications()
  const { data: companies = [] } = useCompanies()
  const { data: languages = [] } = useLanguages()
  const { data: categories = [] } = useJobCategories()
  const { data: sites = [] } = useSites()
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

  const showForm = mode === 'create' || (mode === 'edit' && selectedApplicationId !== null)

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
      siteId: null,
      newLanguage: '',
      newCategory: '',
    },
  })

  useEffect(() => {
    if (mode === 'create') {
      reset({
        companyId: companies[0]?.companyId,
        jobName: '',
        status: 'open',
        langId: languages[0]?.langId ?? null,
        jobCatId: categories[0]?.jobCatId ?? null,
        siteId: null,
        newLanguage: '',
        newCategory: '',
      })
      setLanguageMode(languages[0]?.langId?.toString() ?? ADD_NEW)
      setCategoryMode(categories[0]?.jobCatId?.toString() ?? ADD_NEW)
      return
    }

    if (!selectedApp) {
      reset({ companyId: undefined, jobName: '', status: 'open', langId: null, jobCatId: null, siteId: null, newLanguage: '', newCategory: '' })
      setLanguageMode('')
      setCategoryMode('')
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
      siteId: selectedApp.siteId,
      newLanguage: '',
      newCategory: '',
    })
    setLanguageMode(langMatch ? String(langMatch.langId) : ADD_NEW)
    setCategoryMode(catMatch ? String(catMatch.jobCatId) : ADD_NEW)
  }, [mode, selectedApp, companies, languages, categories, reset])

  async function resolveLanguageAndCategory(values: ApplicationFormValues) {
    let langId = values.langId
    let jobCatId = values.jobCatId

    if (languageMode === ADD_NEW) {
      if (!values.newLanguage?.trim()) {
        setFeedback({ variant: 'error', message: 'Enter a new language or select an existing one.' })
        return null
      }
      const created = await resolveLanguage.mutateAsync(values.newLanguage.trim())
      langId = created.langId
    } else if (languageMode) {
      langId = Number(languageMode)
    }

    if (categoryMode === ADD_NEW) {
      if (!values.newCategory?.trim()) {
        setFeedback({ variant: 'error', message: 'Enter a new category or select an existing one.' })
        return null
      }
      const created = await resolveCategory.mutateAsync(values.newCategory.trim())
      jobCatId = created.jobCatId
    } else if (categoryMode) {
      jobCatId = Number(categoryMode)
    }

    return { langId, jobCatId }
  }

  const onSubmitCreate = handleSubmit(async (values) => {
    setFeedback(null)
    try {
      const resolved = await resolveLanguageAndCategory(values)
      if (!resolved) return

      const created = await createApplication.mutateAsync({
        companyId: values.companyId,
        jobName: values.jobName.trim(),
        status: values.status,
        langId: resolved.langId,
        jobCatId: resolved.jobCatId,
        siteId: values.siteId,
      })

      setSelectedApplicationId(created.applicationId)
      setFeedback({ variant: 'success', message: 'Application created successfully.' })
      onCancel?.()
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Could not create application.'
      setFeedback({ variant: 'error', message })
    }
  })

  const onSubmitUpdate = handleSubmit(async (values) => {
    if (!selectedApplicationId) return
    setFeedback(null)
    try {
      const resolved = await resolveLanguageAndCategory(values)
      if (!resolved) return

      await updateApplication.mutateAsync({
        applicationId: selectedApplicationId,
        companyId: values.companyId,
        jobName: values.jobName.trim(),
        status: values.status,
        langId: resolved.langId,
        jobCatId: resolved.jobCatId,
        siteId: values.siteId,
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
    <Card>
      <CardHeader>
        <CardTitle>{mode === 'create' ? 'New Application' : 'Edit Application'}</CardTitle>
        <CardDescription>
          {mode === 'create'
            ? 'Fill in the details for a new job application.'
            : 'Select an application to load its details, then save your changes.'}
        </CardDescription>
      </CardHeader>

      {mode === 'edit' && (
        <div className="mb-5">
          <Field>
            <Label htmlFor="edit-select">Application</Label>
            <Select
              id="edit-select"
              value={selectedApplicationId ?? ''}
              onChange={(event) => {
                const value = event.target.value
                setFeedback(null)
                setSelectedApplicationId(value ? Number(value) : null)
              }}
            >
              <option value="">— Select an application —</option>
              {applications.map((app) => (
                <option key={app.applicationId} value={app.applicationId}>
                  {applicationLabel(app)}
                </option>
              ))}
            </Select>
          </Field>
        </div>
      )}

      {showForm && (
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

          <Field className="md:col-span-2">
            <Label htmlFor="siteId">Job site (optional)</Label>
            <Select
              id="siteId"
              {...register('siteId', { setValueAs: (v) => (v === '' ? null : Number(v)) })}
            >
              <option value="">— No site linked —</option>
              {sites.map((site) => (
                <option key={site.siteId} value={site.siteId}>
                  {site.address}
                </option>
              ))}
            </Select>
          </Field>

          {feedback ? (
            <div className="md:col-span-2">
              <Alert variant={feedback.variant} message={feedback.message} />
            </div>
          ) : null}

          <div className="flex flex-wrap gap-3 md:col-span-2">
            {mode === 'edit' ? (
              <Button type="button" disabled={isSaving} onClick={onSubmitUpdate}>
                {updateApplication.isPending ? 'Saving...' : 'Save Changes'}
              </Button>
            ) : (
              <>
                <Button type="button" disabled={isSaving} onClick={onSubmitCreate}>
                  {createApplication.isPending ? 'Creating...' : 'Create Application'}
                </Button>
                <Button type="button" variant="secondary" disabled={isSaving} onClick={onCancel}>
                  Cancel
                </Button>
              </>
            )}
          </div>
        </form>
      )}
    </Card>
  )
}

function Milestone1Form() {
  const { data: applications = [], isLoading } = useApplications()
  const [formMode, setFormMode] = useState<AppFormMode>('edit')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted">{applications.length} application{applications.length !== 1 ? 's' : ''}</p>
        {formMode === 'edit' && (
          <Button size="sm" onClick={() => setFormMode('create')}>
            <Plus className="h-4 w-4" />
            New Application
          </Button>
        )}
      </div>

      <DataTable
        isLoading={isLoading}
        data={applications}
        emptyMessage="No applications yet. Use the New Application button above to get started."
        columns={[
          { key: 'jobName', header: 'Position' },
          { key: 'companyName', header: 'Company' },
          { key: 'language', header: 'Language', render: (row) => row.language ?? '—' },
          { key: 'status', header: 'Status' },
          { key: 'categoryName', header: 'Category', render: (row) => row.categoryName ?? '—' },
          {
            key: 'siteAddress',
            header: 'Site',
            render: (row) =>
              row.siteAddress ? (
                <a
                  href={row.siteAddress}
                  target="_blank"
                  rel="noreferrer"
                  className="max-w-[180px] truncate block text-primary hover:underline"
                  title={row.siteAddress}
                >
                  {row.siteAddress}
                </a>
              ) : (
                '—'
              ),
          },
          {
            key: 'createdAt',
            header: 'Created',
            render: (row) => new Date(row.createdAt).toLocaleDateString(),
          },
        ]}
      />

      <ApplicationForm
        mode={formMode}
        onCancel={() => setFormMode('edit')}
      />
    </div>
  )
}

function trackerLabel(row: TrackerWithDetails) {
  return `${row.jobName} | ${row.companyName} | ${new Date(row.createdAt).toLocaleDateString()}`
}

function Milestone2Form() {
  const { data: trackers = [], isLoading } = useTrackers()
  const updateTracker = useUpdateTracker()
  const { selectedApplicationId, setSelectedApplicationId } = useUiStore()
  const [feedback, setFeedback] = useState<{ variant: 'success' | 'error'; message: string } | null>(
    null,
  )

  const selectedTracker = useMemo(
    () => trackers.find((row) => row.applicationId === selectedApplicationId) ?? null,
    [trackers, selectedApplicationId],
  )

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TrackerFormValues>({
    resolver: zodResolver(trackerSchema),
    defaultValues: {
      contactName: '',
      contactEmail: '',
      positionUrl: '',
    },
  })

  useEffect(() => {
    if (!selectedTracker) {
      reset({ contactName: '', contactEmail: '', positionUrl: '' })
      return
    }

    reset({
      contactName: selectedTracker.contactName ?? '',
      contactEmail: selectedTracker.contactEmail ?? '',
      positionUrl: selectedTracker.positionUrl ?? '',
    })
  }, [selectedTracker, reset])

  const onSubmit = handleSubmit(async (values) => {
    if (!selectedApplicationId) {
      setFeedback({ variant: 'error', message: 'Select an application to update tracking.' })
      return
    }

    setFeedback(null)
    try {
      await updateTracker.mutateAsync({
        applicationId: selectedApplicationId,
        contactName: values.contactName?.trim() || null,
        contactEmail: values.contactEmail?.trim() || null,
        positionUrl: values.positionUrl?.trim() || null,
      })
      setFeedback({ variant: 'success', message: 'Tracking details saved successfully.' })
    } catch (error) {
      const message =
        error instanceof ApiClientError ? error.message : 'Could not save tracking details.'
      setFeedback({ variant: 'error', message })
    }
  })

  return (
    <div className="space-y-6">
      <DataTable
        isLoading={isLoading}
        data={trackers}
        emptyMessage="No tracking records yet. Create an application in Milestone 1 first."
        columns={[
          { key: 'companyName', header: 'Company' },
          { key: 'jobName', header: 'Position' },
          { key: 'language', header: 'Language', render: (row) => row.language ?? '—' },
          { key: 'status', header: 'Status' },
          { key: 'categoryName', header: 'Category', render: (row) => row.categoryName ?? '—' },
          { key: 'contactName', header: 'Contact', render: (row) => row.contactName ?? '—' },
          { key: 'contactEmail', header: 'Email', render: (row) => row.contactEmail ?? '—' },
          {
            key: 'positionUrl',
            header: 'Position URL',
            render: (row) =>
              row.positionUrl ? (
                <a
                  href={row.positionUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="text-primary hover:underline"
                >
                  Link
                </a>
              ) : (
                '—'
              ),
          },
        ]}
      />

      <Card>
        <CardHeader>
          <CardTitle>Update Tracking Details</CardTitle>
          <CardDescription>
            Contact person and job posting URL for each application.
          </CardDescription>
        </CardHeader>

        <div className="mb-5">
          <Field>
            <Label htmlFor="tracker-select">Application</Label>
            <Select
              id="tracker-select"
              value={selectedApplicationId ?? ''}
              onChange={(event) => {
                const value = event.target.value
                setSelectedApplicationId(value ? Number(value) : null)
              }}
            >
              <option value="">Select an application...</option>
              {trackers.map((row) => (
                <option key={row.applicationId} value={row.applicationId}>
                  {trackerLabel(row)}
                </option>
              ))}
            </Select>
          </Field>
        </div>

        <form className="grid gap-5 md:grid-cols-2" onSubmit={onSubmit}>
          <Field>
            <Label htmlFor="contactName">Contact name</Label>
            <Input
              id="contactName"
              placeholder="e.g. Jane Recruiter"
              {...register('contactName')}
              error={errors.contactName?.message}
            />
          </Field>

          <Field>
            <Label htmlFor="contactEmail">Contact email</Label>
            <Input
              id="contactEmail"
              type="email"
              placeholder="recruiter@company.com"
              {...register('contactEmail')}
              error={errors.contactEmail?.message}
            />
          </Field>

          <Field className="md:col-span-2">
            <Label htmlFor="positionUrl">Position URL</Label>
            <Input
              id="positionUrl"
              type="url"
              placeholder="https://company.com/jobs/..."
              {...register('positionUrl')}
              error={errors.positionUrl?.message}
            />
          </Field>

          {feedback ? (
            <div className="md:col-span-2">
              <Alert variant={feedback.variant} message={feedback.message} />
            </div>
          ) : null}

          <div className="md:col-span-2">
            <Button type="submit" disabled={updateTracker.isPending || !selectedApplicationId}>
              {updateTracker.isPending ? 'Saving...' : 'Save Tracking Details'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

export function ApplicationsPage() {
  const [activeTab, setActiveTab] = useState<'m1' | 'm2'>('m1')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Applications & Tracking</h1>
        <p className="mt-2 text-muted">
          Manage your application pipeline — create, update, and track each job application.
        </p>
      </div>

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
          Applications
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
          Tracking
        </button>
      </div>

      {activeTab === 'm1' ? <Milestone1Form /> : <Milestone2Form />}
    </div>
  )
}
