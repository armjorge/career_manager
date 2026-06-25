import { cn } from '@/utils/cn'
import type { SelectHTMLAttributes } from 'react'

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  error?: string
}

export function Select({ className, error, children, ...props }: SelectProps) {
  return (
    <div className="space-y-1">
      <select
        className={cn(
          'flex h-10 w-full rounded-lg border bg-surface px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40',
          error ? 'border-danger' : 'border-border',
          className,
        )}
        {...props}
      >
        {children}
      </select>
      {error ? <p className="text-xs text-danger">{error}</p> : null}
    </div>
  )
}
