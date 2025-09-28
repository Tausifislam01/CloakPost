// Cross-bundler env loader (no import.meta.env)
// Priority: window.__ENV -> process.env -> defaults

type EnvShape = { API_BASE?: string; WS_BASE?: string }

declare global {
  interface Window { __ENV?: EnvShape }
}

const trim = (u?: string | null) => (u ? u.replace(/\/$/, '') : undefined)

function fromWindow(): EnvShape {
  if (typeof window !== 'undefined' && window.__ENV) return window.__ENV
  return {}
}

function fromProcess(): EnvShape {
  // Avoid referencing the global `process` identifier directly so this file
  // type-checks in browser-focused TS setups without Node types.
  const anyGlobal: any = globalThis as any
  const anyProc: any = (typeof anyGlobal.process !== 'undefined' ? anyGlobal.process : {})
  const env: any = anyProc?.env || {}
  return {
    API_BASE: env.VITE_API_BASE || env.REACT_APP_API_BASE || env.API_BASE,
    WS_BASE: env.VITE_WS_BASE || env.REACT_APP_WS_BASE || env.WS_BASE
  }
}

const win = fromWindow()
const proc = fromProcess()
const defHttp = typeof window !== 'undefined' ? window.location.origin : ''
const defWs = typeof window !== 'undefined' ? window.location.origin.replace(/^http/, 'ws') : ''

export const API_BASE = trim(win.API_BASE || proc.API_BASE || defHttp)!
export const WS_BASE = trim(win.WS_BASE || proc.WS_BASE || defWs)!
