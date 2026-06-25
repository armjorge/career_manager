import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { AuthProvider, useAuth } from '@/context/AuthContext'
import { AppShell } from '@/layouts/AppShell'
import { Auth } from '@/pages/Auth'
import { DashboardPage } from '@/pages/DashboardPage'
import { CompaniesPage } from '@/pages/companies/CompaniesPage'
import { ApplicationsPage } from '@/pages/applications/ApplicationsPage'
import { PlaceholderPage } from '@/pages/PlaceholderPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

function AuthGate() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex items-center gap-3 text-sm text-muted">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          Loading session...
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Auth />
  }

  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="companies" element={<CompaniesPage />} />
        <Route path="applications" element={<ApplicationsPage />} />
        <Route
          path="documents"
          element={
            <PlaceholderPage
              title="Letters & CV"
              description="Resume details, cover letters, and template management."
            />
          }
        />
        <Route
          path="generator"
          element={
            <PlaceholderPage
              title="Document Generator"
              description="Generate Word documents from templates and saved application content."
            />
          }
        />
        <Route
          path="sites"
          element={
            <PlaceholderPage
              title="Website Repository"
              description="Manage job search bookmarks and application portals."
            />
          }
        />
        <Route
          path="analytics"
          element={
            <PlaceholderPage
              title="Analytics"
              description="Pipeline metrics, monthly trends, and strategic insights."
            />
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <AuthGate />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
