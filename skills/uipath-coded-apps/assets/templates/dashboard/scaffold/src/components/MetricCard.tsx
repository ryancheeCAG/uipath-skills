import React from 'react'

interface MetricCardProps {
  title: string
  value: string | number
  delta?: string
  loading?: boolean
  error?: string | null
}

export default function MetricCard({ title, value, delta, loading, error }: MetricCardProps) {
  return (
    <div className="rounded-lg border bg-card p-4 space-y-1">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
        {title}
      </p>
      {loading ? (
        <div className="h-8 w-24 animate-pulse rounded bg-muted" />
      ) : error ? (
        <p className="text-sm text-destructive">{error}</p>
      ) : (
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-semibold">{value}</span>
          {delta && (
            <span className="text-xs text-muted-foreground">{delta}</span>
          )}
        </div>
      )}
    </div>
  )
}
