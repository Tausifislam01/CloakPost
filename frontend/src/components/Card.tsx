import React from 'react'

export default function Card({
  children,
  className = '',
}: {
  children: React.ReactNode
  className?: string
}) {
  return <div className={`bg-white rounded-2xl border shadow-sm ${className}`}>{children}</div>
}
