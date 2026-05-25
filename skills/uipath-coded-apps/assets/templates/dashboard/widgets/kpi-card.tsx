import React from 'react'
import MetricCard from '../components/MetricCard'
// IMPORT: import { useInsights } from '../hooks/useInsights'

export function <COMPONENT_NAME>() {
  const { data, loading, error } = <DATA_HOOK>

  const value = data
    ? String((data as Record<string, unknown>)['<VALUE_KEY>'] ?? '—')
    : '—'

  return (
    <MetricCard
      title="<TITLE>"
      value={value}
      loading={loading}
      error={error?.message}
    />
  )
}
