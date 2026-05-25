import React from 'react'
import type { UiPathSDKConfig } from '@uipath/uipath-typescript/core'
import { AuthProvider, useAuth } from './hooks/useAuth'
import DashboardShell from './components/DashboardShell'

const sdkConfig: UiPathSDKConfig = {
  clientId: import.meta.env.VITE_UIPATH_CLIENT_ID as string,
  scopes: (import.meta.env.VITE_UIPATH_SCOPE as string).split(' '),
  organizationName: import.meta.env.VITE_UIPATH_ORG_NAME as string,
  tenantName: import.meta.env.VITE_UIPATH_TENANT_NAME as string,
  baseUrl: import.meta.env.VITE_UIPATH_BASE_URL as string,
}

function AppContent() {
  const { isAuthenticated, isLoading, login, error } = useAuth()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground text-sm">Loading…</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center space-y-4">
          {error && <p className="text-destructive text-sm">{error}</p>}
          <button
            onClick={() => void login()}
            className="rounded-md bg-primary px-6 py-2 text-primary-foreground text-sm font-medium hover:opacity-90"
          >
            Sign in with UiPath
          </button>
        </div>
      </div>
    )
  }

  return <DashboardShell />
}

export default function App() {
  return (
    <AuthProvider config={sdkConfig}>
      <AppContent />
    </AuthProvider>
  )
}
