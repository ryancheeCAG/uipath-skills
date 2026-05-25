import React from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { useInsights } from '../hooks/useInsights'

export function <COMPONENT_NAME>() {
  const { data, loading, error } = <DATA_HOOK>

  if (loading) return <div className="h-64 animate-pulse rounded-lg bg-muted" />
  if (error) return <div className="rounded-lg border bg-card p-4 text-sm text-destructive">{error.message}</div>

  return (
    <div className="rounded-lg border bg-card p-4">
      <h3 className="mb-3 text-sm font-medium text-muted-foreground"><TITLE></h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data as Record<string, unknown>[]}>
          <XAxis dataKey="<X_KEY>" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey="<Y_KEY>" fill="hsl(var(--primary))" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
