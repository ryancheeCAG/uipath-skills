import React, { useState, useEffect, useRef, createContext, useContext, useCallback } from 'react'
import type { ReactNode } from 'react'
import { UiPath } from '@uipath/uipath-typescript/core'
import type { UiPathSDKConfig } from '@uipath/uipath-typescript/core'

interface AuthContextType {
  isAuthenticated: boolean
  isLoading: boolean
  sdk: UiPath
  tenantId: string
  getToken: () => Promise<string>
  login: () => Promise<void>
  error: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const SCOPES = 'OR.Assets OR.Assets.Read OR.Jobs OR.Jobs.Write OR.Folders OR.Folders.Read OR.Buckets OR.Buckets.Read OR.Execution OR.Execution.Read OR.Tasks OR.Tasks.Write OR.Queues OR.Queues.Read OR.Users OR.Users.Read DataFabric.Schema.Read DataFabric.Data.Read DataFabric.Data.Write PIMS Insights.RealTimeData ConversationalAgents Traces.Api openid profile'

function resolveConfig(): UiPathSDKConfig {
  const platformHosted =
    document.querySelector('meta[name="uipath:platform-hosted"]')?.getAttribute('content') === 'true'

  return {
    baseUrl:     import.meta.env.VITE_UIPATH_BASE_URL as string,
    orgName:     import.meta.env.VITE_UIPATH_ORG_NAME as string,
    tenantName:  import.meta.env.VITE_UIPATH_TENANT_NAME as string,
    clientId:    import.meta.env.VITE_UIPATH_CLIENT_ID as string,
    scopes:      SCOPES.split(' '),
    redirectUri: `${window.location.origin}${window.location.pathname}`,
    platformHosted,
  }
}

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [{ config, sdk }] = useState(() => {
    const config = resolveConfig()
    return { config, sdk: new UiPath(config) }
  })
  const didInit = useRef(false)

  useEffect(() => {
    if (didInit.current) return
    didInit.current = true

    const init = async () => {
      setIsLoading(true)
      setError(null)
      try {
        if (config.platformHosted) {
          // FP surface mode: wait for UIP.init from host (no sign-in button).
          // EmbeddedTokenManager sets isAuthenticated() once UIP.init arrives.
          // Timeout after 9 seconds (matches SDK's requestHostToken timeout).
          await new Promise<void>((resolve, reject) => {
            let poll: ReturnType<typeof setInterval>
            const timer = setTimeout(() => {
              clearInterval(poll)
              reject(new Error('UIP.init timeout — host did not send token'))
            }, 9000)
            poll = setInterval(() => {
              if (sdk.isAuthenticated()) {
                clearTimeout(timer)
                clearInterval(poll)
                resolve()
              }
            }, 100)
          })
          setIsAuthenticated(true)
        } else {
          // Local preview mode: OAuth PKCE
          if (sdk.isInOAuthCallback()) {
            await sdk.completeOAuth()
            window.history.replaceState({}, document.title, window.location.pathname)
          }
          setIsAuthenticated(sdk.isAuthenticated())
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Authentication failed')
      } finally {
        setIsLoading(false)
      }
    }

    void init()
    return () => {
      didInit.current = false
      sdk.destroy()
    }
  }, [sdk])

  const getToken = useCallback(async (): Promise<string> => {
    const token = sdk.getToken()
    if (token) return token
    throw new Error('Access token not available — please sign in')
  }, [sdk])

  const login = useCallback(async () => {
    await sdk.login()
  }, [sdk])

  const value: AuthContextType = {
    isAuthenticated,
    isLoading,
    sdk,
    tenantId: import.meta.env.VITE_INSIGHTS_TENANT_ID as string,
    getToken,
    login,
    error,
  }

  return React.createElement(AuthContext.Provider, { value }, children)
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
