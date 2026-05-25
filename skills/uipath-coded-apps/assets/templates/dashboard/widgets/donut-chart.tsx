import React from 'react'
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useInsights } from '../hooks/useInsights'

const COLORS = [
  'hsl(var(--primary))',
  'hsl(215 100% 60%)',
  'hsl(150 60% 50%)',
  'hsl(30 100% 60%)',
]

export function <COMPONENT_NAME>() {
  const { data, loading, error } = <DATA_HOOK>

  if (loading) return <div className="h-64 animate-pulse rounded-lg bg-muted" />
  if (error) return <div className="rounded-lg border bg-card p-4 text-sm text-destructive">{error.message}</div>

  const chartData = Array.isArray(data)
    ? data
    : Object.entries(data as Record<string, number>).map(([name, value]) => ({ name, value }))

  return (
    <div className="rounded-lg border bg-card p-4">
      <h3 className="mb-3 text-sm font-medium text-muted-foreground"><TITLE></h3>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={chartData as Record<string, unknown>[]}
            dataKey="<DATA_KEY>"
            nameKey="<NAME_KEY>"
            innerRadius={60}
            outerRadius={90}
          >
            {(chartData as Record<string, unknown>[]).map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
