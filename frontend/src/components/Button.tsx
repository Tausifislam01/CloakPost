import React from 'react'

export default function Button(
  props: React.ButtonHTMLAttributes<HTMLButtonElement> & { loading?: boolean }
) {
  const { className = '', loading, children, ...rest } = props
  return (
    <button
      className={`px-4 py-2 rounded-xl bg-black text-white hover:opacity-90 disabled:opacity-60 ${className}`}
      disabled={loading || rest.disabled}
      {...rest}
    >
      {loading ? '…' : children}
    </button>
  )
}
