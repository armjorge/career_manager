import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Alert } from '@/components/ui/Alert'

export function PlaceholderPage({
  title,
  description,
}: {
  title: string
  description: string
}) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        <p className="mt-2 text-muted">{description}</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Coming in Sprint 2</CardTitle>
          <CardDescription>
            This route is wired in the router and ready for implementation against the same mock API
            pattern used by Companies and Applications.
          </CardDescription>
        </CardHeader>
        <Alert variant="info" message="UI shell is live — business forms will be added next." />
      </Card>
    </div>
  )
}
