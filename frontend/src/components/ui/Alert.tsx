import { cn } from '@/utils/cn'
import { AlertCircle, CheckCircle2, Info } from 'lucide-react'

type AlertVariant = 'info' | 'success' | 'warning' | 'error'

interface AlertProps {
  variant?: AlertVariant
  title?: string
  message: string
  className?: string
}

const variantStyles: Record<AlertVariant, string> = {
  info: 'border-primary/30 bg-primary/10 text-foreground',
  success: 'border-success/30 bg-success/10 text-foreground',
  warning: 'border-warning/30 bg-warning/10 text-foreground',
  error: 'border-danger/30 bg-danger/10 text-foreground',
}

const icons: Record<AlertVariant, typeof Info> = {
  info: Info,
  success: CheckCircle2,
  warning: AlertCircle,
  error: AlertCircle,
}

export function Alert({ variant = 'info', title, message, className }: AlertProps) {
  const Icon = icons[variant]
  return (
    <div className={cn('flex gap-3 rounded-lg border p-4 text-sm', variantStyles[variant], className)}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div>
        {title ? <p className="font-medium">{title}</p> : null}
        <p className={title ? 'mt-1 text-muted' : undefined}>{message}</p>
      </div>
    </div>
  )
}
