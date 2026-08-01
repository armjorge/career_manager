import { NavLink, Outlet } from 'react-router-dom'
import {
  BarChart3,
  Building2,
  FileText,
  FolderOpen,
  Globe,
  LayoutDashboard,
  LogOut,
  Paperclip,
  Rocket,
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { isMockMode } from '@/api/client'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/auth/useAuth'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/companies', label: 'Companies', icon: Building2 },
  { to: '/applications', label: 'Applications', icon: FileText },
  { to: '/documents', label: 'Letters & CV', icon: FolderOpen },
  { to: '/attachments', label: 'App PDFs', icon: Paperclip },
  { to: '/generator', label: 'Generator', icon: Rocket },
  { to: '/sites', label: 'Web Pages', icon: Globe },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
]

export function AppShell() {
  const { user, signOut } = useAuth()

  return (
    <div className="flex min-h-screen flex-col lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="shrink-0 border-b border-border bg-surface lg:border-b-0 lg:border-r">
        <div className="flex flex-col lg:h-full lg:min-h-screen">
          <div className="hidden border-b border-border px-5 py-6 lg:block">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/15 text-primary">
                <Rocket className="h-5 w-5" />
              </div>
              <div>
                <p className="font-semibold text-foreground">Career Manager</p>
                <p className="text-xs text-muted">Application pipeline</p>
              </div>
            </div>
            {isMockMode ? (
              <span className="mt-3 inline-flex rounded-full bg-warning/15 px-2.5 py-1 text-[11px] font-medium text-warning">
                Mock API
              </span>
            ) : null}
          </div>

          <div className="flex items-center justify-between px-4 py-3 lg:hidden">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15 text-primary">
                <Rocket className="h-4 w-4" />
              </div>
              <p className="font-semibold text-foreground">Career Manager</p>
              {isMockMode ? (
                <span className="inline-flex rounded-full bg-warning/15 px-2 py-0.5 text-[11px] font-medium text-warning">
                  Mock
                </span>
              ) : null}
            </div>
            <Button type="button" variant="ghost" size="sm" onClick={() => signOut()}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>

          <nav className="flex gap-1 overflow-x-auto p-2 lg:flex-1 lg:flex-col lg:overflow-visible lg:p-3">
            {navItems.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn(
                    'flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors lg:gap-3 lg:py-2.5',
                    isActive
                      ? 'bg-primary/15 text-primary'
                      : 'text-muted hover:bg-surface-elevated hover:text-foreground',
                  )
                }
              >
                <Icon className="h-4 w-4 shrink-0" />
                {label}
              </NavLink>
            ))}
          </nav>

          <div className="mt-auto hidden border-t border-border p-4 lg:block">
            <div className="mb-3 min-w-0">
              <p className="truncate text-sm font-medium text-foreground">
                {user?.email ?? 'Signed in'}
              </p>
              <p className="truncate text-xs text-muted">{user?.sub}</p>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="w-full justify-start"
              onClick={() => signOut()}
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </Button>
          </div>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
