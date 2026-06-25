import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppShell } from '@/layouts/AppShell'
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

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
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
      </BrowserRouter>
    </QueryClientProvider>
  )
}
