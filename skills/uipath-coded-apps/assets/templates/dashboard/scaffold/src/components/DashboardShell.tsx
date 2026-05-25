import React from 'react'
import WidgetGrid from './WidgetGrid'

interface NavItem {
  label: string
  id: string
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Overview', id: 'overview' },
]

export default function DashboardShell({ children }: { children?: React.ReactNode }) {
  const [active, setActive] = React.useState('overview')

  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Sidebar */}
      <aside className="w-56 border-r flex flex-col py-4 px-3 gap-1 shrink-0">
        <div className="text-sm font-semibold px-2 py-1 mb-2 text-muted-foreground uppercase tracking-wide">
          Dashboard
        </div>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => setActive(item.id)}
            className={`text-sm px-3 py-2 rounded-md text-left transition-colors ${
              active === item.id
                ? 'bg-primary text-primary-foreground'
                : 'hover:bg-muted text-foreground'
            }`}
          >
            {item.label}
          </button>
        ))}
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto p-6">
        <WidgetGrid>{children}</WidgetGrid>
      </main>
    </div>
  )
}
