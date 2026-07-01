import { useRef, useState } from 'react'
import { Upload, Download, Trash2, CheckCircle, Clock } from 'lucide-react'
import { ApiClientError } from '@/api/client'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Field, Label } from '@/components/ui/Label'
import { Select } from '@/components/ui/Select'
import {
  useAttachments,
  useDeleteAttachment,
  useDownloadAttachment,
  useUploadAttachment,
} from '@/hooks/useDocuments'
import { useApplications } from '@/hooks/useApplications'
import type { ApplicationWithDetails, Attachment, AttachmentType } from '@/types'
import { ATTACHMENT_LABELS, ATTACHMENT_TYPES } from '@/types'

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function applicationLabel(app: ApplicationWithDetails) {
  return `${app.companyName} — ${app.jobName} (#${app.applicationId})`
}

interface AttachmentCardProps {
  applicationId: number
  attachmentType: AttachmentType
  attachment: Attachment | undefined
}

function AttachmentCard({ applicationId, attachmentType, attachment }: AttachmentCardProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const upload = useUploadAttachment(applicationId)
  const remove = useDeleteAttachment(applicationId)
  const download = useDownloadAttachment()
  const [feedback, setFeedback] = useState<{ variant: 'success' | 'error'; message: string } | null>(null)

  const hasFile = Boolean(attachment?.s3Key)
  const label = ATTACHMENT_LABELS[attachmentType]

  const onUpload = async (file: File | undefined) => {
    if (!file) return
    setFeedback(null)
    try {
      await upload.mutateAsync({ attachmentType, file })
      setFeedback({ variant: 'success', message: `${label} uploaded successfully.` })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Upload failed.'
      setFeedback({ variant: 'error', message })
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const onDelete = async () => {
    setFeedback(null)
    try {
      await remove.mutateAsync(attachmentType)
      setFeedback({ variant: 'success', message: `${label} removed.` })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Failed to remove.'
      setFeedback({ variant: 'error', message })
    }
  }

  const onDownload = async () => {
    setFeedback(null)
    try {
      const result = await download.mutateAsync({ applicationId, attachmentType })
      window.open(result.downloadUrl, '_blank', 'noopener,noreferrer')
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Failed to get download URL.'
      setFeedback({ variant: 'error', message })
    }
  }

  return (
    <div className="rounded-lg border border-border bg-background p-4">
      {/* Header row */}
      <div className="flex items-start gap-3">
        <div className="mt-0.5 shrink-0">
          {hasFile ? (
            <CheckCircle className="h-5 w-5 text-green-500" />
          ) : (
            <Clock className="h-5 w-5 text-muted" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-medium text-foreground">{label}</p>
          {hasFile && attachment ? (
            <p className="mt-0.5 truncate text-xs text-muted">
              {attachment.fileName}
              {attachment.fileSizeBytes != null ? ` · ${formatBytes(attachment.fileSizeBytes)}` : ''}
              {attachment.uploadedAt ? ` · ${new Date(attachment.uploadedAt).toLocaleDateString()}` : ''}
            </p>
          ) : (
            <p className="mt-0.5 text-xs text-muted">No file uploaded</p>
          )}
        </div>
      </div>

      {/* Feedback */}
      {feedback ? (
        <div className="mt-3">
          <Alert variant={feedback.variant} message={feedback.message} />
        </div>
      ) : null}

      {/* Actions */}
      <div className="mt-3 flex flex-wrap gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(event) => void onUpload(event.target.files?.[0])}
        />
        <Button
          type="button"
          size="sm"
          variant="secondary"
          onClick={() => fileInputRef.current?.click()}
          disabled={upload.isPending}
        >
          <Upload className="h-3.5 w-3.5" />
          {hasFile ? 'Replace' : 'Upload'}
        </Button>

        {hasFile ? (
          <>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              onClick={() => void onDownload()}
              disabled={download.isPending}
            >
              <Download className="h-3.5 w-3.5" />
              Download
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => void onDelete()}
              disabled={remove.isPending}
            >
              <Trash2 className="h-3.5 w-3.5" />
              Remove
            </Button>
          </>
        ) : null}
      </div>
    </div>
  )
}

interface AttachmentPanelProps {
  applicationId: number
}

function AttachmentPanel({ applicationId }: AttachmentPanelProps) {
  const { data: attachments = [], isLoading } = useAttachments(applicationId)

  const attachmentMap = Object.fromEntries(
    attachments.map((a) => [a.attachmentType, a]),
  ) as Record<AttachmentType, Attachment | undefined>

  if (isLoading) {
    return <p className="text-sm text-muted">Loading attachments…</p>
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {ATTACHMENT_TYPES.map((type) => (
        <AttachmentCard
          key={type}
          applicationId={applicationId}
          attachmentType={type}
          attachment={attachmentMap[type]}
        />
      ))}
    </div>
  )
}

export function AttachmentsPage() {
  const { data: applications = [], isLoading: appsLoading } = useApplications()
  const [selectedId, setSelectedId] = useState<number | ''>('')

  const selected = applications.find((a) => a.applicationId === selectedId) ?? null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Application PDFs</h1>
        <p className="mt-1 text-sm text-muted">
          Upload, replace, or remove the job description, submitted CV, and cover letter PDFs for each application.
          Files are stored in S3 and tracked in the database.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Select application</CardTitle>
          <CardDescription>Choose a job application to manage its attached PDFs.</CardDescription>
        </CardHeader>
        <div className="px-6 pb-6">
          <Field>
            <Label htmlFor="attach-app-select">Application</Label>
            {appsLoading ? (
              <p className="text-sm text-muted">Loading applications…</p>
            ) : (
              <Select
                id="attach-app-select"
                value={selectedId === '' ? '' : String(selectedId)}
                onChange={(event) => setSelectedId(event.target.value ? Number(event.target.value) : '')}
              >
                <option value="">Select application…</option>
                {applications.map((app) => (
                  <option key={app.applicationId} value={app.applicationId}>
                    {applicationLabel(app)}
                  </option>
                ))}
              </Select>
            )}
          </Field>
        </div>
      </Card>

      {selected !== null && selectedId !== '' ? (
        <Card>
          <CardHeader>
            <CardTitle>
              {selected.companyName} — {selected.jobName}
            </CardTitle>
            <CardDescription>
              Manage the three PDF slots for this application. PDFs are stored in S3; the slot remains tracked
              even when empty.
            </CardDescription>
          </CardHeader>
          <div className="px-6 pb-6">
            <AttachmentPanel applicationId={selectedId as number} />
          </div>
        </Card>
      ) : null}
    </div>
  )
}
