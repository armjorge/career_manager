import { NavLink, Outlet } from 'react-router-dom'
import {
  BarChart3,
  Building2,
  FileText,
  FolderOpen,
  Globe,
  LayoutDashboard,
  Rocket,
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { isMockMode } from '@/api/client'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/companies', label: 'Companies', icon: Building2 },
  { to: '/applications', label: 'Applications', icon: FileText },
  { to: '/documents', label: 'Letters & CV', icon: FolderOpen },
  { to: '/generator', label: 'Generator', icon: Rocket },
  { to: '/sites', label: 'Web Pages', icon: Globe },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
]

export function AppShell() {
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
      <aside className="border-b border-border bg-surface lg:border-b-0 lg:border-r">
        <div className="flex h-full flex-col">
          <div className="border-b border-border px-5 py-6">
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

          <nav className="flex gap-1 overflow-x-auto p-3 lg:flex-col lg:overflow-visible">
            {navItems.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium whitespace-nowrap transition-colors',
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
        </div>
      </aside>

      <main className="min-w-0">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
