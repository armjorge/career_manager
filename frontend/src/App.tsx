import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from '@/context/AuthContext'
import { AppShell } from '@/layouts/AppShell'
import { Auth } from '@/pages/Auth'
import { DashboardPage } from '@/pages/DashboardPage'
import { CompaniesPage } from '@/pages/companies/CompaniesPage'
import { ApplicationsPage } from '@/pages/applications/ApplicationsPage'
import { AnalyticsPage } from '@/pages/AnalyticsPage'
import { DocumentsPage } from '@/pages/documents/DocumentsPage'
import { GeneratorPage } from '@/pages/documents/GeneratorPage'
import { AttachmentsPage } from '@/pages/documents/AttachmentsPage'
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
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <Auth />
  }

  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="companies" element={<CompaniesPage />} />
        <Route path="applications" element={<ApplicationsPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="generator" element={<GeneratorPage />} />
        <Route path="attachments" element={<AttachmentsPage />} />
        <Route
          path="sites"
          element={
            <PlaceholderPage
              title="Website Repository"
              description="Manage job search bookmarks and application portals."
            />
          }
        />
        <Route path="analytics" element={<AnalyticsPage />} />
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
