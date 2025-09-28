import { WS_BASE } from './env'
const join = (b: string, p: string) => `${b}${p.startsWith('/') ? '' : '/'}${p}`

// Accept either numeric peer id or username string; callers may pass either
export function chatSocketByPeerId(peerId: string | number): WebSocket {
  return new WebSocket(join(WS_BASE, `/ws/chat/${encodeURIComponent(String(peerId))}/`))
}
