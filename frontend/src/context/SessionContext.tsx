import React, { createContext, useContext, useEffect, useState } from 'react'
import { isLoggedIn } from '../lib/auth'

interface SessionCtx { loggedIn: boolean; setLoggedIn: (v: boolean) => void }
const Ctx = createContext<SessionCtx | null>(null)

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [loggedIn, setLoggedIn] = useState(isLoggedIn())
  useEffect(() => {
    const i = setInterval(() => setLoggedIn(isLoggedIn()), 3000)
    return () => clearInterval(i)
  }, [])
  return <Ctx.Provider value={{ loggedIn, setLoggedIn }}>{children}</Ctx.Provider>
}

export function useSession() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useSession must be used within SessionProvider')
  return ctx
}
