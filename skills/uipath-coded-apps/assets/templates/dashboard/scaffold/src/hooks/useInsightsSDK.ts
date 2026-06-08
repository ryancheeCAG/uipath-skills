import { useState, useEffect } from 'react'
import { useAuth } from './useAuth'
import type { UiPath } from '@uipath/uipath-typescript/core'

/**
 * Hook for fetching data from Insights SDK service methods.
 *
 * Usage:
 *   const { data, loading, error } = useInsightsSDK<AgentErrorsResponse>(
 *     sdk => new AgentsInsights(sdk).getErrors({ startTime: THIRTY_DAYS_AGO, endTime: NOW }),
 *     []
 *   )
 *
 * The fetcher receives the authenticated SDK instance.
 * Results are typed by the generic parameter T.
 * The SDK service class must be constructed with `new ServiceClass(sdk as never)`.
 *
 * @template T - The response type returned by the Insights SDK method
 * @param fetcher - Function that calls the SDK service method
 * @param deps - Dependency array for re-fetching (defaults to fetcher identity)
 */
export function useInsightsSDK<T>(
  fetcher: (sdk: UiPath) => Promise<T>,
  deps: unknown[] = []
) {
  const { sdk } = useAuth()
  const [data, setData]       = useState<T | null>(null)
  const [error, setError]     = useState<Error | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!sdk) return

    let cancelled = false
    setLoading(true)
    setError(null)

    fetcher(sdk)
      .then(result => { if (!cancelled) { setData(result); setLoading(false) } })
      .catch(err   => { if (!cancelled) { setError(err instanceof Error ? err : new Error(String(err))); setLoading(false) } })

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps.length > 0 ? deps : [])

  return { data, error, loading }
}
