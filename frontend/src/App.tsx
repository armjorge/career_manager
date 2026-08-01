import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { AuthProvider } from './auth/AuthContext'
import { RedirectIfAuthenticated, RequireAuth } from './auth/RequireAuth'
import { AppShell } from './layouts/AppShell'
import { AuthCallbackPage } from './pages/AuthCallbackPage'
import { ForgotPasswordPage } from './pages/ForgotPasswordPage'
import { LoginPage } from './pages/LoginPage'
import { SignupPage } from './pages/SignupPage'
import { DashboardPage } from './pages/DashboardPage'
import { CompaniesPage } from './pages/companies/CompaniesPage'
import { ApplicationsPage } from './pages/applications/ApplicationsPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { DocumentsPage } from './pages/documents/DocumentsPage'
import { GeneratorPage } from './pages/documents/GeneratorPage'
import { AttachmentsPage } from './pages/documents/AttachmentsPage'
import { SitesPage } from './pages/sites/SitesPage'
import { PostHogProvider } from './providers/PostHogProvider'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

export default function App() {
  return (
    <PostHogProvider>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <Routes>
              <Route
                path="/login"
                element={
                  <RedirectIfAuthenticated>
                    <LoginPage />
                  </RedirectIfAuthenticated>
                }
              />
              <Route
                path="/signup"
                element={
                  <RedirectIfAuthenticated>
                    <SignupPage />
                  </RedirectIfAuthenticated>
                }
              />
              <Route
                path="/forgot-password"
                element={
                  <RedirectIfAuthenticated>
                    <ForgotPasswordPage />
                  </RedirectIfAuthenticated>
                }
              />
              <Route path="/auth/callback" element={<AuthCallbackPage />} />
              <Route
                element={
                  <RequireAuth>
                    <AppShell />
                  </RequireAuth>
                }
              >
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
            </Routes>
          </BrowserRouter>
        </QueryClientProvider>
      </AuthProvider>
    </PostHogProvider>
  )
}
