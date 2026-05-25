import React from 'react'
import { HashRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { ErrorBoundary } from './dashboard/chrome/ErrorBoundary'
import { LoadingState } from './dashboard/chrome/LoadingState'

// Dashboard + views are generated per-build by the skill agent.
// The agent will add imports and routes below when building.
// DO NOT DELETE these comment markers — the agent uses them to inject code.

// GENERATED_IMPORTS_START
// GENERATED_IMPORTS_END

function AppContent() {
  const { isAuthenticated, isLoading, error } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoadingState height="h-20" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-8">
        <div className="text-center space-y-2">
          <p className="text-destructive font-medium">Authentication error</p>
          <p className="text-sm text-muted-foreground">{error}</p>
          <p className="text-xs text-muted-foreground mt-2">
            For local preview: set <code className="bg-muted px-1 rounded">VITE_UIPATH_PAT</code> in <code className="bg-muted px-1 rounded">.env.local</code>
          </p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-sm text-muted-foreground">Waiting for authentication…</p>
      </div>
    )
  }

  return (
    <HashRouter>
      <Routes>
        {/* GENERATED_ROUTES_START */}
        {/* GENERATED_ROUTES_END */}
      </Routes>
    </HashRouter>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  )
}
