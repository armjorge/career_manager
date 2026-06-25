import { cn } from '@/utils/cn'

interface Column<T> {
  key: keyof T | string
  header: string
  render?: (row: T) => React.ReactNode
  className?: string
}

interface DataTableProps<T extends object> {
  columns: Column<T>[]
  data: T[]
  emptyMessage?: string
  isLoading?: boolean
}

export function DataTable<T extends object>({
  columns,
  data,
  emptyMessage = 'No records found.',
  isLoading = false,
}: DataTableProps<T>) {
  if (isLoading) {
    return (
      <div className="rounded-lg border border-border bg-surface-elevated/40 p-8 text-center text-sm text-muted">
        Loading...
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-surface-elevated/20 p-8 text-center text-sm text-muted">
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-border text-sm">
          <thead className="bg-surface-elevated/80">
            <tr>
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className={cn('px-4 py-3 text-left font-medium text-muted', column.className)}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border bg-surface">
            {data.map((row, index) => (
              <tr key={index} className="hover:bg-surface-elevated/40">
                {columns.map((column) => (
                  <td key={String(column.key)} className={cn('px-4 py-3 text-foreground', column.className)}>
                    {column.render
                      ? column.render(row)
                      : String((row as Record<string, unknown>)[column.key as string] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
