import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ExternalLink, Trash2 } from 'lucide-react'
import { ApiClientError } from '@/api/client'
import { Alert } from '@/components/ui/Alert'
import { Button } from '@/components/ui/Button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { DataTable } from '@/components/data/DataTable'
import { Field, Label } from '@/components/ui/Label'
import { Input } from '@/components/ui/Input'
import { useSites, useCreateSite, useDeleteSite } from '@/hooks/useSites'

const siteSchema = z.object({
  address: z.string().trim().min(1, 'URL is required'),
})

type SiteFormValues = z.infer<typeof siteSchema>

export function SitesPage() {
  const { data: sites = [], isLoading } = useSites()
  const createSite = useCreateSite()
  const deleteSite = useDeleteSite()
  const [feedback, setFeedback] = useState<{ variant: 'success' | 'error'; message: string } | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SiteFormValues>({
    resolver: zodResolver(siteSchema),
    defaultValues: { address: '' },
  })

  const onSubmit = handleSubmit(async (values) => {
    setFeedback(null)
    try {
      await createSite.mutateAsync(values.address)
      reset()
      setFeedback({ variant: 'success', message: 'Site added successfully.' })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Could not add site.'
      setFeedback({ variant: 'error', message })
    }
  })

  const handleDelete = async (siteId: number) => {
    setDeletingId(siteId)
    setFeedback(null)
    try {
      await deleteSite.mutateAsync(siteId)
      setFeedback({ variant: 'success', message: 'Site removed.' })
    } catch (error) {
      const message = error instanceof ApiClientError ? error.message : 'Could not remove site.'
      setFeedback({ variant: 'error', message })
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Website Repository</h1>
        <p className="mt-2 text-muted">
          Manage job boards and application portals. Link a site to any application in Milestone 1.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Saved Sites</CardTitle>
          <CardDescription>
            URLs ordered by most recently added. Sites with active applications cannot be deleted
            until all linked applications are updated.
          </CardDescription>
        </CardHeader>

        <DataTable
          isLoading={isLoading}
          data={sites}
          emptyMessage="No sites saved yet. Add your first job board below."
          columns={[
            {
              key: 'address',
              header: 'Address',
              render: (row) => (
                <a
                  href={row.address}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5 text-primary hover:underline"
                >
                  <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                  <span className="truncate max-w-[420px]">{row.address}</span>
                </a>
              ),
            },
            {
              key: 'applicationCount',
              header: 'Applications',
              render: (row) => (
                <span className={row.applicationCount > 0 ? 'font-medium text-foreground' : 'text-muted'}>
                  {row.applicationCount}
                </span>
              ),
            },
            {
              key: 'createdAt',
              header: 'Added',
              render: (row) => new Date(row.createdAt).toLocaleDateString(),
            },
            {
              key: 'siteId',
              header: '',
              render: (row) => (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={deletingId === row.siteId || row.applicationCount > 0}
                  title={
                    row.applicationCount > 0
                      ? 'Cannot delete — linked to active applications'
                      : 'Delete site'
                  }
                  onClick={() => void handleDelete(row.siteId)}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              ),
            },
          ]}
        />

        <form onSubmit={onSubmit} className="mt-4 space-y-3 border-t border-border pt-4 md:max-w-xl">
          <Field>
            <Label htmlFor="address">Add new site</Label>
            <Input
              id="address"
              placeholder="https://linkedin.com/jobs"
              {...register('address')}
              error={errors.address?.message}
            />
          </Field>

          {feedback ? <Alert variant={feedback.variant} message={feedback.message} /> : null}

          <Button type="submit" disabled={createSite.isPending}>
            {createSite.isPending ? 'Adding...' : 'Add Site'}
          </Button>
        </form>
      </Card>
    </div>
  )
}
