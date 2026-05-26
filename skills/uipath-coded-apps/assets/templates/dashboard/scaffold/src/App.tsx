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

  const didTriggerLogin = React.useRef(false)

  React.useEffect(() => {
    if (isLoading || isAuthenticated || error) return
    // If the OAuth callback is being processed (code= in URL), useAuth handles it — don't re-redirect
    const inCallback = window.location.search.includes('code=') || window.location.search.includes('state=')
    if (inCallback || didTriggerLogin.current) return
    didTriggerLogin.current = true
    void login()
  }, [isLoading, isAuthenticated, error, login])

  if (isLoading || (!isAuthenticated && !error)) {
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
