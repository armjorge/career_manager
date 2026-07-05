import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { NeonAuthUIProvider } from '@neondatabase/auth-ui'
import { authClient } from '@/auth/client'
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
import { SitesPage } from '@/pages/sites/SitesPage'
import { ResetPasswordPage } from '@/pages/ResetPasswordPage'

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

  return (
    <Routes>
      <Route path="reset-password" element={<ResetPasswordPage />} />
      {isAuthenticated ? (
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="companies" element={<CompaniesPage />} />
          <Route path="applications" element={<ApplicationsPage />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="generator" element={<GeneratorPage />} />
          <Route path="attachments" element={<AttachmentsPage />} />
          <Route path="sites" element={<SitesPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      ) : (
        <Route path="*" element={<Auth />} />
      )}
    </Routes>
  )
}

export default function App() {
  return (
    <NeonAuthUIProvider authClient={authClient} redirectTo="/" defaultTheme="dark">
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <BrowserRouter>
            <AuthGate />
          </BrowserRouter>
        </AuthProvider>
      </QueryClientProvider>
    </NeonAuthUIProvider>
  )
}
