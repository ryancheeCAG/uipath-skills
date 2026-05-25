import React from 'react'

interface WidgetGridProps {
  children?: React.ReactNode
}

export default function WidgetGrid({ children }: WidgetGridProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {children}
    </div>
  )
}
