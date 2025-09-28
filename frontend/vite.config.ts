import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Allow setting a custom base path at build time via VITE_BASE environment
// variable. Defaults to '/' which is appropriate for root deployments.
const anyGlobal: any = globalThis as any
const base = (typeof anyGlobal.process !== 'undefined' && anyGlobal.process.env?.VITE_BASE) || '/'

// cast to any to allow the `test` field for Vitest without pulling node types
export default defineConfig({
  base,
  plugins: [react()],
  server: { port: 5173, host: true },
  // Use jsdom so Vitest tests that rely on the DOM (React components) work.
  test: { environment: 'jsdom' }
} as any)
