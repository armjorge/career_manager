import { useEffect, useMemo, useRef, useState } from 'react'
import { ApiClientError } from '@/api/client'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { DataTable } from '@/components/data/DataTable'
import { Field, Label } from '@/components/ui/Label'
import { Select } from '@/components/ui/Select'
import {
  useCoverLetterRows,
  useDeleteTemplate,
  useResumeRows,
  useTemplates,
  useUpdateCoverLetter,
  useUpdateResumeDetails,
  useUpdateTemplate,
  useUploadTemplate,
} from '@/hooks/useDocuments'
import { useLanguages } from '@/hooks/useCompanies'
import type { CoverLetterRow, FileTemplate, FileType, ResumeDetailsRow } from '@/types'

function applicationLabel(row: { jobName: string; companyName: string; createdAt: string }) {
  return `${row.jobName} | ${row.companyName} | ${new Date(row.createdAt).toLocaleDateString()}`
}

function ResumeTab() {
  const { data: rows = [], isLoading } = useResumeRows()
  const { data: templates = [] } = useTemplates()
  const updateResume = useUpdateResumeDetails()
  const [selectedId, setSelectedId] = useState<number | ''>('')
  const [feedback, setFeedback] = useState<{ variant: 'success' | 'error'; message: string } | null>(null)
  const [form, setForm] = useState({
    ed1: '',
    ed2: '',
    ed3: '',
    ex1: '',
    ex2: '',
    ex3: '',
    skills: '',
    interests: '',
    fileId: '' as number | '',
  })

  const cvTemplates = useMemo(
    () => templates.filter((item) => item.fileType === 'cv'),
    [templates],
  )

  const selectedRow = useMemo(
    () => rows.find((row) => row.applicationId === selectedId) ?? null,
    [rows, selectedId],
  )

  useEffect(() => {
    if (!selectedRow) {
      setForm({
        ed1: '',
        ed2: '',
        ed3: '',
        ex1: '',
        ex2: '',
        ex3: '',
        skills: '',
        interests: '',
        fileId: '',
      })
      return
    }
    setForm({
      ed1: selectedRow.ed1 ?? '',
      ed2: selectedRow.ed2 ?? '',
      ed3: selectedRow.ed3 ?? '',
      ex1: selectedRow.ex1 ?? '',
      ex2: selectedRow.ex2 ?? '',
      ex3: selectedRow.ex3 ?? '',
      skills: selectedRow.skills ?? '',
      interests: selectedRow.interests ?? '',
      fileId: selectedRow.fileId ?? '',
    })
  }, [selectedRow])

  const onSave = async () => {
    if (!selectedId) {
      setFeedback({ variant: 'error', message: 'Select an application first.' })
      return
    }
    setFeedback(null)
    try {
      await updateResume.mutateAsync({
        applicationId: selectedId,
        ed1: form.ed1 || null,
        ed2: form.ed2 || null,
        ed3: form.ed3 || null,
        ex1: form.ex1 || null,
        ex2: form.ex2 || null,
        ex3: form.ex3 || null,
        skills: form.skills || null,
        interests: form.interests || null,
        fileId: form.fileId === '' ? null : Number(form.fileId),
      })
      setFeedback({ variant: 'success', message: 'Resume details saved.' })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Failed to save resume details.'
      setFeedback({ variant: 'error', message })
    }
  }

  return (
    <div className="space-y-6">
      <DataTable<ResumeDetailsRow>
        isLoading={isLoading}
        emptyMessage="No applications found for resume filling."
        columns={[
          { key: 'companyName', header: 'Company' },
          { key: 'jobName', header: 'Job' },
          { key: 'language', header: 'Language' },
          { key: 'status', header: 'Status' },
          { key: 'categoryName', header: 'Category' },
          { key: 'fileName', header: 'Template' },
        ]}
        data={rows}
      />

      <Card>
        <CardHeader>
          <CardTitle>Fill / update resume details</CardTitle>
          <CardDescription>
            Map education, experience, skills, and interests to placeholders like {'{ex1}'} in your CV template.
          </CardDescription>
        </CardHeader>
        <div className="space-y-4 px-6 pb-6">
          {feedback ? <Alert variant={feedback.variant} message={feedback.message} /> : null}

          <Field>
            <Label htmlFor="resume-app">Application</Label>
            <Select
              id="resume-app"
              value={selectedId === '' ? '' : String(selectedId)}
              onChange={(event) => setSelectedId(event.target.value ? Number(event.target.value) : '')}
            >
              <option value="">Select application…</option>
              {rows.map((row) => (
                <option key={row.applicationId} value={row.applicationId}>
                  {applicationLabel(row)}
                </option>
              ))}
            </Select>
          </Field>

          <div className="grid gap-4 md:grid-cols-2">
            {(['ed1', 'ed2', 'ed3', 'ex1', 'ex2', 'ex3', 'skills', 'interests'] as const).map((field) => (
              <Field key={field}>
                <Label htmlFor={`resume-${field}`}>{field.toUpperCase()}</Label>
                <textarea
                  id={`resume-${field}`}
                  className="min-h-24 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                  value={form[field]}
                  onChange={(event) => setForm((current) => ({ ...current, [field]: event.target.value }))}
                />
              </Field>
            ))}
          </div>

          <Field>
            <Label htmlFor="resume-template">Associated template (CV)</Label>
            <Select
              id="resume-template"
              value={form.fileId === '' ? '' : String(form.fileId)}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  fileId: event.target.value ? Number(event.target.value) : '',
                }))
              }
            >
              <option value="">No template</option>
              {cvTemplates.map((template) => (
                <option key={template.fileId} value={template.fileId}>
                  {template.fileName}
                </option>
              ))}
            </Select>
          </Field>

          <Button type="button" onClick={() => void onSave()} disabled={updateResume.isPending}>
            Save resume details
          </Button>
        </div>
      </Card>
    </div>
  )
}

function CoverLetterTab() {
  const { data: rows = [], isLoading } = useCoverLetterRows()
  const { data: templates = [] } = useTemplates()
  const updateCoverLetter = useUpdateCoverLetter()
  const [selectedId, setSelectedId] = useState<number | ''>('')
  const [feedback, setFeedback] = useState<{ variant: 'success' | 'error'; message: string } | null>(null)
  const [form, setForm] = useState({ header: '', body: '', close: '', fileId: '' as number | '' })

  const clTemplates = useMemo(
    () => templates.filter((item) => item.fileType === 'cover letter'),
    [templates],
  )

  const selectedRow = useMemo(
    () => rows.find((row) => row.applicationId === selectedId) ?? null,
    [rows, selectedId],
  )

  useEffect(() => {
    if (!selectedRow) {
      setForm({ header: '', body: '', close: '', fileId: '' })
      return
    }
    setForm({
      header: selectedRow.header ?? '',
      body: selectedRow.body ?? '',
      close: selectedRow.close ?? '',
      fileId: selectedRow.fileId ?? '',
    })
  }, [selectedRow])

  const onSave = async () => {
    if (!selectedId) {
      setFeedback({ variant: 'error', message: 'Select an application first.' })
      return
    }
    setFeedback(null)
    try {
      await updateCoverLetter.mutateAsync({
        applicationId: selectedId,
        header: form.header || null,
        body: form.body || null,
        close: form.close || null,
        fileId: form.fileId === '' ? null : Number(form.fileId),
      })
      setFeedback({ variant: 'success', message: 'Cover letter saved.' })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Failed to save cover letter.'
      setFeedback({ variant: 'error', message })
    }
  }

  return (
    <div className="space-y-6">
      <DataTable<CoverLetterRow>
        isLoading={isLoading}
        emptyMessage="No applications found for cover letter filling."
        columns={[
          { key: 'companyName', header: 'Company' },
          { key: 'jobName', header: 'Job' },
          { key: 'language', header: 'Language' },
          { key: 'status', header: 'Status' },
          { key: 'categoryName', header: 'Category' },
          { key: 'fileName', header: 'Template' },
        ]}
        data={rows}
      />

      <Card>
        <CardHeader>
          <CardTitle>Fill / update cover letter</CardTitle>
          <CardDescription>Header, body, and closing map to placeholders in your cover letter template.</CardDescription>
        </CardHeader>
        <div className="space-y-4 px-6 pb-6">
          {feedback ? <Alert variant={feedback.variant} message={feedback.message} /> : null}

          <Field>
            <Label htmlFor="cover-app">Application</Label>
            <Select
              id="cover-app"
              value={selectedId === '' ? '' : String(selectedId)}
              onChange={(event) => setSelectedId(event.target.value ? Number(event.target.value) : '')}
            >
              <option value="">Select application…</option>
              {rows.map((row) => (
                <option key={row.applicationId} value={row.applicationId}>
                  {applicationLabel(row)}
                </option>
              ))}
            </Select>
          </Field>

          {(['header', 'body', 'close'] as const).map((field) => (
            <Field key={field}>
              <Label htmlFor={`cover-${field}`}>{field.charAt(0).toUpperCase() + field.slice(1)}</Label>
              <textarea
                id={`cover-${field}`}
                className="min-h-24 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
                value={form[field]}
                onChange={(event) => setForm((current) => ({ ...current, [field]: event.target.value }))}
              />
            </Field>
          ))}

          <Field>
            <Label htmlFor="cover-template">Associated template (cover letter)</Label>
            <Select
              id="cover-template"
              value={form.fileId === '' ? '' : String(form.fileId)}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  fileId: event.target.value ? Number(event.target.value) : '',
                }))
              }
            >
              <option value="">No template</option>
              {clTemplates.map((template) => (
                <option key={template.fileId} value={template.fileId}>
                  {template.fileName}
                </option>
              ))}
            </Select>
          </Field>

          <Button type="button" onClick={() => void onSave()} disabled={updateCoverLetter.isPending}>
            Save cover letter
          </Button>
        </div>
      </Card>
    </div>
  )
}

function TemplatesSection() {
  const { data: templates = [], isLoading } = useTemplates()
  const { data: languages = [] } = useLanguages()
  const uploadTemplate = useUploadTemplate()
  const updateTemplate = useUpdateTemplate()
  const deleteTemplate = useDeleteTemplate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [feedback, setFeedback] = useState<{ variant: 'success' | 'error'; message: string } | null>(null)
  const [drafts, setDrafts] = useState<Record<number, { fileType: FileType; langId: string }>>({})

  useEffect(() => {
    const next: Record<number, { fileType: FileType; langId: string }> = {}
    for (const template of templates) {
      next[template.fileId] = {
        fileType: template.fileType,
        langId: template.langId ? String(template.langId) : '',
      }
    }
    setDrafts(next)
  }, [templates])

  const onUpload = async (file: File | undefined) => {
    if (!file) return
    setFeedback(null)
    try {
      await uploadTemplate.mutateAsync(file)
      setFeedback({ variant: 'success', message: `Uploaded ${file.name}` })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Upload failed.'
      setFeedback({ variant: 'error', message })
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const onSaveTemplate = async (template: FileTemplate) => {
    const draft = drafts[template.fileId]
    if (!draft) return
    setFeedback(null)
    try {
      await updateTemplate.mutateAsync({
        fileId: template.fileId,
        fileType: draft.fileType,
        langId: draft.langId ? Number(draft.langId) : null,
      })
      setFeedback({ variant: 'success', message: `Updated ${template.fileName}` })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Failed to update template.'
      setFeedback({ variant: 'error', message })
    }
  }

  const onRemoveTemplate = async (template: FileTemplate) => {
    setFeedback(null)
    try {
      await deleteTemplate.mutateAsync(template.fileId)
      setFeedback({ variant: 'success', message: `Removed ${template.fileName}` })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Failed to remove template.'
      setFeedback({ variant: 'error', message })
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Template management</CardTitle>
        <CardDescription>
          Upload .docx templates to S3 under your user folder. Files are tracked in dim_file with hash-based deduplication.
        </CardDescription>
      </CardHeader>
      <div className="space-y-4 px-6 pb-6">
        {feedback ? <Alert variant={feedback.variant} message={feedback.message} /> : null}

        <div className="flex flex-wrap items-center gap-3">
          <input
            ref={fileInputRef}
            type="file"
            accept=".docx"
            className="hidden"
            onChange={(event) => void onUpload(event.target.files?.[0])}
          />
          <Button type="button" variant="secondary" onClick={() => fileInputRef.current?.click()}>
            Upload template
          </Button>
        </div>

        {isLoading ? (
          <p className="text-sm text-muted">Loading templates…</p>
        ) : templates.length === 0 ? (
          <p className="text-sm text-muted">No active templates. Upload a .docx file to get started.</p>
        ) : (
          <div className="space-y-3">
            {templates.map((template) => {
              const draft = drafts[template.fileId]
              return (
                <div
                  key={template.fileId}
                  className="grid gap-3 rounded-lg border border-border p-4 md:grid-cols-[1.5fr_1fr_1fr_auto_auto]"
                >
                  <div>
                    <p className="font-medium text-foreground">{template.fileName}</p>
                    <p className="text-xs text-muted">Hash: {template.fileHash.slice(0, 8)}…</p>
                  </div>
                  <Select
                    value={draft?.fileType ?? template.fileType}
                    onChange={(event) =>
                      setDrafts((current) => ({
                        ...current,
                        [template.fileId]: {
                          fileType: event.target.value as FileType,
                          langId: draft?.langId ?? '',
                        },
                      }))
                    }
                  >
                    <option value="cv">cv</option>
                    <option value="cover letter">cover letter</option>
                  </Select>
                  <Select
                    value={draft?.langId ?? ''}
                    onChange={(event) =>
                      setDrafts((current) => ({
                        ...current,
                        [template.fileId]: {
                          fileType: draft?.fileType ?? template.fileType,
                          langId: event.target.value,
                        },
                      }))
                    }
                  >
                    <option value="">No language</option>
                    {languages.map((language) => (
                      <option key={language.langId} value={language.langId}>
                        {language.language}
                      </option>
                    ))}
                  </Select>
                  <Button type="button" size="sm" onClick={() => void onSaveTemplate(template)}>
                    Save
                  </Button>
                  <Button type="button" size="sm" variant="ghost" onClick={() => void onRemoveTemplate(template)}>
                    Remove
                  </Button>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </Card>
  )
}

export function DocumentsPage() {
  const [tab, setTab] = useState<'resume' | 'cover'>('resume')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Letters & CV</h1>
        <p className="mt-1 text-sm text-muted">
          Manage resume blocks, cover letters, and Word templates for document generation.
        </p>
      </div>

      <div className="flex gap-2 border-b border-border">
        <button
          type="button"
          className={`px-4 py-2 text-sm font-medium ${tab === 'resume' ? 'border-b-2 border-primary text-primary' : 'text-muted'}`}
          onClick={() => setTab('resume')}
        >
          Resume details
        </button>
        <button
          type="button"
          className={`px-4 py-2 text-sm font-medium ${tab === 'cover' ? 'border-b-2 border-primary text-primary' : 'text-muted'}`}
          onClick={() => setTab('cover')}
        >
          Cover letter
        </button>
      </div>

      {tab === 'resume' ? <ResumeTab /> : <CoverLetterTab />}
      <TemplatesSection />
    </div>
  )
}
