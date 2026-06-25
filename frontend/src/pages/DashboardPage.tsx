import { Link } from 'react-router-dom'
import { ArrowRight, Building2, FileText, FolderOpen, Globe, Rocket } from 'lucide-react'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { isMockMode } from '@/api/client'

const sections = [
  {
    to: '/companies',
    title: 'Companies',
    description: 'Manage company types, languages, and target organizations.',
    icon: Building2,
  },
  {
    to: '/applications',
    title: 'Applications',
    description: 'Create applications and track recruiter contact details.',
    icon: FileText,
  },
  {
    to: '/documents',
    title: 'Letters & CV',
    description: 'Fill resume and cover letter content for each application.',
    icon: FolderOpen,
  },
  {
    to: '/generator',
    title: 'Generator',
    description: 'Generate Word documents from templates and saved content.',
    icon: Rocket,
  },
  {
    to: '/sites',
    title: 'Web Pages',
    description: 'Maintain your job search website bookmarks.',
    icon: Globe,
  },
]

export function DashboardPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Career Manager Dashboard</h1>
        <p className="mt-2 max-w-2xl text-muted">
          Select a section to continue managing your job applications, document pipeline, and
          outreach workflow.
        </p>
        {isMockMode ? (
          <p className="mt-3 text-sm text-warning">
            Running with in-memory mock data. Connect FastAPI later via{' '}
            <code className="rounded bg-surface-elevated px-1.5 py-0.5">VITE_API_BASE_URL</code>.
          </p>
        ) : null}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {sections.map(({ to, title, description, icon: Icon }) => (
          <Link key={to} to={to} className="group">
            <Card className="h-full transition-colors group-hover:border-primary/40 group-hover:bg-surface-elevated/40">
              <CardHeader>
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
                <CardTitle>{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </CardHeader>
              <div className="flex items-center gap-2 text-sm font-medium text-primary">
                Open section
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
