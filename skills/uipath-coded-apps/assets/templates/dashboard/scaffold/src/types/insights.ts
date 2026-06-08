/**
 * Insights response type stubs.
 *
 * These will be replaced by SDK imports once Insights ships in the TypeScript SDK:
 *   import type { AgentErrorsResponse, ... } from '@uipath/uipath-typescript/insights'
 */

// ── Agents namespace ──────────────────────────────────────────────────────────

export interface AgentErrorItem {
  name: string
  value: number
  date: string
}

export interface AgentErrorsResponse {
  data: AgentErrorItem[]
  totalErrors?: number
}

export interface ConsumptionPoint {
  timeSlice: string
  aguConsumption: number
}

export interface ConsumptionTimelineResponse {
  data: ConsumptionPoint[]
}

export interface AgentRankedItem {
  name: string
  count: number
}

export interface TopErroredAgentsResponse {
  data: AgentRankedItem[]
  totalErrors?: number
}

export interface AgentItem {
  agentId: string
  agentName: string
  folderPath: string
  lastRun: string
  healthScore: number
  lastIncidentType: string
  unitsQuantity: number
  quantityAGU: number
}

export interface AgentsResponse {
  data: {
    agents: AgentItem[]
    totalAGUUnitsConsumed: number
    totalPLTUUnitsConsumed: number
    totalUnitsConsumed: number
  }
  pagination?: { totalCount: number; pageNumber: number; pageSize: number }
}

export interface LatencyPoint {
  name: 'P50' | 'P95'
  value: number
  date: string
}

export interface LatencyTimelineResponse {
  data: LatencyPoint[]
}

// ── Jobs namespace ────────────────────────────────────────────────────────────

export interface JobRankedItem {
  processName: string
  failureCount: number
}

export interface TopFailuresResponse {
  data: JobRankedItem[]
}

export interface JobCompletionPoint {
  date: string
  count: number
  state: 'Successful' | 'Faulted' | 'Stopped'
}

export interface CompletedTimelineResponse {
  data: JobCompletionPoint[]
}
