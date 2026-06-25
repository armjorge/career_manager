import { cn } from '@/utils/cn'
import { Check } from 'lucide-react'

const milestones = [
  { id: 'm1', label: 'Application', short: 'M1' },
  { id: 'm2', label: 'Tracking', short: 'M2' },
  { id: 'm3', label: 'Resume', short: 'M3' },
  { id: 'm4', label: 'Cover Letter', short: 'M4' },
  { id: 'm5', label: 'Generate', short: 'M5' },
] as const

interface MilestoneStepperProps {
  completed: Record<(typeof milestones)[number]['id'], boolean>
  active?: (typeof milestones)[number]['id']
}

export function MilestoneStepper({ completed, active = 'm1' }: MilestoneStepperProps) {
  return (
    <ol className="flex flex-wrap items-center gap-2">
      {milestones.map((step, index) => {
        const isComplete = completed[step.id]
        const isActive = step.id === active
        return (
          <li key={step.id} className="flex items-center gap-2">
            <div
              className={cn(
                'flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors',
                isComplete && 'border-success/40 bg-success/10 text-success',
                isActive && !isComplete && 'border-primary/40 bg-primary/10 text-primary',
                !isComplete && !isActive && 'border-border bg-surface text-muted',
              )}
            >
              <span
                className={cn(
                  'flex h-5 w-5 items-center justify-center rounded-full text-[10px]',
                  isComplete ? 'bg-success text-white' : isActive ? 'bg-primary text-white' : 'bg-surface-elevated',
                )}
              >
                {isComplete ? <Check className="h-3 w-3" /> : step.short}
              </span>
              <span className="hidden sm:inline">{step.label}</span>
            </div>
            {index < milestones.length - 1 ? (
              <span className="hidden h-px w-4 bg-border sm:block" aria-hidden />
            ) : null}
          </li>
        )
      })}
    </ol>
  )
}

export function defaultMilestoneProgress() {
  return { m1: false, m2: false, m3: false, m4: false, m5: false }
}
