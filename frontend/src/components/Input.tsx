import React from 'react'

export default function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  const { className = '', ...rest } = props
  return (
    <input
      className={`w-full px-3 py-2 rounded-xl border focus:outline-none focus:ring focus:ring-gray-200 ${className}`}
      {...rest}
    />
  )
}
