/**
 * Insights response type stubs.
 *
 * These mirror the actual types exported by the SDK's Insights services.
 * Replace this file with direct SDK imports when the packages are published:
 *
 *   import type { AgentErrorsTimelineResponse } from '@uipath/uipath-typescript/agents'
 *   import type { GovernanceOperationSummary }  from '@uipath/uipath-typescript/governance'
 *   import type { MemoryTimelinePoint }         from '@uipath/uipath-typescript/memory'
 */

// ── Agents service (@uipath/uipath-typescript/agents) ────────────────────────

/** getErrorsTimeline() — /Agents/errors */
export interface AgentErrorItem { name: string; value: number; date: string }
export interface AgentErrorsTimelineResponse { data: AgentErrorItem[] }

/** getConsumptionTimeline() — /Agents/consumptionTimeline */
export interface ConsumptionPoint { timeSlice: string; aguConsumption: number }
export interface AgentConsumptionTimelineResponse { data: ConsumptionPoint[] }

/** getTopErroredAgents() — /Agents/topErroredAgents */
export interface AgentRankedItem { name: string; count: number }
export interface AgentTopErroredAgentsResponse { data: AgentRankedItem[] }

/** getAll() — /Agents/agents (paginated) */
export interface AgentListItem {
  agentId: string; agentName: string; folderPath: string
  lastRun: string; healthScore: number; lastIncidentType: string
  unitsQuantity: number; quantityAGU: number
}
export interface AgentListTotals {
  totalAGUUnitsConsumed: number; totalPLTUUnitsConsumed: number; totalUnitsConsumed: number
}
export interface AgentListResponse { items: AgentListItem[]; totalCount?: number }

/** getLatencyTimeline() — /Agents/latencyTimeline */
export interface LatencyPoint { name: 'P50' | 'P95'; value: number; date: string }
export interface AgentLatencyTimelineResponse { data: LatencyPoint[] }

// ── Jobs Insights service (@uipath/uipath-typescript/jobs-insights) ──────────
// Note: import path pending SDK release confirmation

/** getTopFailures() */
export interface JobRankedItem { processName: string; failureCount: number }
export interface JobTopFailuresResponse { data: JobRankedItem[] }

/** getCompletedTimeline() */
export interface JobCompletionPoint { date: string; count: number; state: 'Successful' | 'Faulted' | 'Stopped' }
export interface JobCompletedTimelineResponse { data: JobCompletionPoint[] }

// ── Jobs service (@uipath/uipath-typescript/jobs) ─────────────────────────────
// Note: These types mirror JobGetResponse from the SDK for dashboard display

/** getAll() filtered response item */
export interface JobDisplayItem {
  key?: string
  state?: string
  processName?: string
  startTime?: Date | string
  endTime?: Date | string
  createdTime?: Date | string
}

export interface PaginatedJobsResponse {
  items?: JobDisplayItem[]
  value?: JobDisplayItem[]
}

// ── Governance service (@uipath/uipath-typescript/governance) ────────────────

/** getOperationSummary() — /Governance/operation/summary */
export interface GovernanceOperationSummary {
  totalEvaluations: number; allow: number; deny: number; noOp: number
}

/** getPolicyTraces() — /Governance/policy/traces (paginated) */
export interface PolicyTrace {
  traceId: string; policyId: string; policyEvaluationResult: string
  agentId?: string; userId?: string; timestamp: string
}

// ── Memory service (@uipath/uipath-typescript/memory) ────────────────────────

/** getTimeline() — /Traceview/memoryTimeline (bare array, envelope unwrapped) */
export interface MemoryTimelinePoint { timeSlice: string; inMemoryCount: number }

/** getCallsTimeline() — /Traceview/memoryCallsTimeline */
export interface MemoryCallsTimelinePoint { timeSlice: string; memoryCallsCount: number }

/** getTopSpaces() — /Traceview/topMemorySpaces */
export interface MemorySpace { memorySpaceName: string; memoryCount: number }
