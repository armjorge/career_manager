import { useMemo, useState } from 'react'
import { ApiClientError } from '@/api/client'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { DataTable } from '@/components/data/DataTable'
import { Field, Label } from '@/components/ui/Label'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import {
  useDeleteGeneration,
  useDownloadGeneration,
  useGenerateDocument,
  useGenerationOptions,
  useGenerations,
} from '@/hooks/useDocuments'
import type { DocumentCategory, GenerationLog, GenerationOption } from '@/types'

function optionLabel(option: GenerationOption) {
  return `${option.companyName} | ${option.jobName} (${option.language ?? 'Unknown'})`
}

function proposeFilename(prefix: string, option: GenerationOption) {
  const catSuffix = option.category === 'Resume' ? 'CV' : 'CLetter'
  const role = option.categoryName ?? catSuffix
  const parts = [prefix.trim(), option.companyName, role].filter(Boolean)
  return `${parts.join(' ')}.docx`
}

export function GeneratorPage() {
  const { data: options = [], isLoading: optionsLoading } = useGenerationOptions()
  const { data: generations = [], isLoading: historyLoading } = useGenerations(50)
  const generateDocument = useGenerateDocument()
  const downloadGeneration = useDownloadGeneration()
  const deleteGeneration = useDeleteGeneration()

  const [category, setCategory] = useState<DocumentCategory>('Resume')
  const [selectedKey, setSelectedKey] = useState('')
  const [prefix, setPrefix] = useState('')
  const [historyFilter, setHistoryFilter] = useState('')
  const [feedback, setFeedback] = useState<{ variant: 'success' | 'error'; message: string } | null>(null)

  const filteredOptions = useMemo(
    () => options.filter((option) => option.category === category),
    [options, category],
  )

  const selectedOption = useMemo(() => {
    if (!selectedKey) return null
    return filteredOptions.find((option) => `${option.applicationId}` === selectedKey) ?? null
  }, [filteredOptions, selectedKey])

  const proposedFilename = selectedOption ? proposeFilename(prefix, selectedOption) : null

  const filteredGenerations = useMemo(() => {
    const q = historyFilter.trim().toLowerCase()
    if (!q) return generations
    return generations.filter((row) =>
      [row.companyName, row.jobName, row.outputFile]
        .filter(Boolean)
        .some((field) => field!.toLowerCase().includes(q)),
    )
  }, [generations, historyFilter])

  const onGenerate = async () => {
    if (!selectedOption) {
      setFeedback({ variant: 'error', message: 'Select an application with an active template.' })
      return
    }
    setFeedback(null)
    try {
      const result = await generateDocument.mutateAsync({
        applicationId: selectedOption.applicationId,
        category,
        prefix: prefix.trim() || null,
      })
      setFeedback({
        variant: 'success',
        message: result.pdfSuccess
          ? `Document generated: ${result.outputFile}`
          : 'Generation recorded as failed.',
      })
      if (result.downloadUrl) {
        window.open(result.downloadUrl, '_blank', 'noopener,noreferrer')
      }
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Document generation failed.'
      setFeedback({ variant: 'error', message })
    }
  }

  const onDownload = async (row: GenerationLog) => {
    setFeedback(null)
    try {
      const result = await downloadGeneration.mutateAsync(row.pdfId)
      if (result.downloadUrl === '#') {
        setFeedback({ variant: 'success', message: `Mock download: ${result.fileName}` })
        return
      }
      window.open(result.downloadUrl, '_blank', 'noopener,noreferrer')
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Download failed.'
      setFeedback({ variant: 'error', message })
    }
  }

  const onDelete = async (row: GenerationLog) => {
    setFeedback(null)
    try {
      await deleteGeneration.mutateAsync(row.pdfId)
      setFeedback({ variant: 'success', message: `Removed ${row.outputFile}` })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Failed to remove generation record.'
      setFeedback({ variant: 'error', message })
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Document generator</h1>
        <p className="mt-1 text-sm text-muted">
          Generate Word documents from linked templates and saved resume or cover letter content.
        </p>
      </div>

      {feedback ? <Alert variant={feedback.variant} message={feedback.message} /> : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Selection</CardTitle>
            <CardDescription>Only applications with an active linked template appear here.</CardDescription>
          </CardHeader>
          <div className="space-y-4 px-6 pb-6">
            <div className="flex gap-4">
              {(['Resume', 'Cover Letter'] as const).map((value) => (
                <label key={value} className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="category"
                    checked={category === value}
                    onChange={() => {
                      setCategory(value)
                      setSelectedKey('')
                    }}
                  />
                  {value}
                </label>
              ))}
            </div>

            {optionsLoading ? (
              <p className="text-sm text-muted">Loading options…</p>
            ) : filteredOptions.length === 0 ? (
              <p className="text-sm text-muted">No active templates for {category}. Link a template in Letters & CV.</p>
            ) : (
              <Field>
                <Label htmlFor="generator-app">Application</Label>
                <Select
                  id="generator-app"
                  value={selectedKey}
                  onChange={(event) => setSelectedKey(event.target.value)}
                >
                  <option value="">Select application…</option>
                  {filteredOptions.map((option) => (
                    <option key={option.applicationId} value={option.applicationId}>
                      {optionLabel(option)}
                    </option>
                  ))}
                </Select>
              </Field>
            )}

            {selectedOption ? (
              <p className="text-sm text-muted">
                Template: <span className="text-foreground">{selectedOption.fileName}</span>
              </p>
            ) : null}
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
            <CardDescription>Output name uses prefix, company, and job category with duplicate suffixes.</CardDescription>
          </CardHeader>
          <div className="space-y-4 px-6 pb-6">
            <Field>
              <Label htmlFor="generator-prefix">Filename prefix (optional)</Label>
              <Input
                id="generator-prefix"
                placeholder="e.g. JACJ"
                value={prefix}
                onChange={(event) => setPrefix(event.target.value)}
              />
            </Field>

            {proposedFilename ? (
              <p className="text-sm text-muted">
                Proposed output: <code className="text-foreground">{proposedFilename}</code>
              </p>
            ) : null}

            <Button type="button" onClick={() => void onGenerate()} disabled={generateDocument.isPending}>
              Generate document
            </Button>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Generated documents</CardTitle>
          <CardDescription>Logged in fact_pdf_generator. Download opens a pre-signed S3 link.</CardDescription>
        </CardHeader>
        <div className="space-y-4 px-6 pb-6">
          <Input
            placeholder="Filter by company, job, or filename…"
            value={historyFilter}
            onChange={(e) => setHistoryFilter(e.target.value)}
          />
          <DataTable<GenerationLog>
            isLoading={historyLoading}
            emptyMessage={historyFilter ? 'No results match your filter.' : 'No documents generated yet.'}
            columns={[
              {
                key: 'companyName',
                header: 'Company',
                render: (row) => row.companyName ?? '—',
              },
              {
                key: 'jobName',
                header: 'Job',
                render: (row) => row.jobName ?? '—',
              },
              { key: 'outputFile', header: 'Output file' },
              {
                key: 'pdfSuccess',
                header: 'OK',
                render: (row) => (row.pdfSuccess ? 'Yes' : 'No'),
              },
              {
                key: 'createdAt',
                header: 'Created',
                render: (row) => new Date(row.createdAt).toLocaleString(),
              },
              {
                key: 'pdfId',
                header: '',
                render: (row) => (
                  <div className="flex gap-2">
                    {row.pdfSuccess ? (
                      <Button type="button" size="sm" variant="secondary" onClick={() => void onDownload(row)}>
                        Download
                      </Button>
                    ) : null}
                    <Button type="button" size="sm" variant="danger" onClick={() => void onDelete(row)}>
                      Remove
                    </Button>
                  </div>
                ),
              },
            ]}
            data={filteredGenerations}
          />
        </div>
      </Card>
    </div>
  )
}
