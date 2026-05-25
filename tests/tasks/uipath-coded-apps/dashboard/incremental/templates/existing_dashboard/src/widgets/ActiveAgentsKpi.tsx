import React from 'react'
import { useInsights } from '../hooks/useInsights'

interface AgentsResponse {
  data: { agents: Array<{ agentId: string }> }
}

export function ActiveAgentsKpi() {
  const startTime = new Date(Date.now() - 2592000000).toISOString()
  const { data, loading, error } = useInsights<AgentsResponse>('agents.getAgents', { startTime })
  const count = data?.data?.agents?.length ?? '—'
  if (loading) return <div className="h-20 animate-pulse rounded-lg bg-muted" />
  if (error) return <div className="text-destructive text-sm">{error.message}</div>
  return <div className="rounded-lg border bg-card p-4"><p className="text-2xl font-semibold">{count}</p><p className="text-sm text-muted-foreground">Active Agents</p></div>
}
