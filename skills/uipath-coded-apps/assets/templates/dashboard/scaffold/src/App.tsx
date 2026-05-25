import React from 'react'
import { AuthProvider, useAuth } from './hooks/useAuth'
import DashboardShell from './components/DashboardShell'

function AppContent() {
  const { isAuthenticated, isLoading, error } = useAuth()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-muted-foreground text-sm">Connecting…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center space-y-2">
          <p className="text-destructive text-sm font-medium">Auth error</p>
          <p className="text-muted-foreground text-xs max-w-sm">{error}</p>
          <p className="text-muted-foreground text-xs">
            For local dev: set <code className="bg-muted px-1 rounded">VITE_UIPATH_PAT</code> in{' '}
            <code className="bg-muted px-1 rounded">.env.local</code>
          </p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <p className="text-muted-foreground text-sm">Waiting for authentication…</p>
      </div>
    )
  }

  return <DashboardShell />
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
