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
  const { isAuthenticated, isLoading, error, login } = useAuth()

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
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    const platformHosted =
      document.querySelector('meta[name="uipath:platform-hosted"]')?.getAttribute('content') === 'true'

    if (platformHosted) {
      return (
        <div className="min-h-screen bg-background flex items-center justify-center">
          <p className="text-sm text-muted-foreground">
            {error || 'Waiting for authentication from host…'}
          </p>
        </div>
      )
    }

    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
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
