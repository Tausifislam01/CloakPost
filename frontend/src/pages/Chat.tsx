// change route to /chat/:peerId and this file:
import { useEffect, useMemo, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import Card from '../components/Card'
import Button from '../components/Button'
import Input from '../components/Input'
import { chatSocketByPeerId } from '../lib/ws'

export default function Chat() {
  const { peerId = '' } = useParams()
  const numericId = Number(peerId)
  const [messages, setMessages] = useState<Array<{ from: string; text: string; at: string }>>([])
  const [text, setText] = useState('')
  const wsRef = useRef<WebSocket | null>(null)

  const ws = useMemo(() => chatSocketByPeerId(numericId), [numericId])

  useEffect(() => {
    wsRef.current = ws
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data)
        // Backend broadcasts { type: "chat.message", sender_username, plaintext }
        if (data.type === 'chat.message') {
          setMessages((m) => [
            ...m,
            { from: data.sender_username, text: data.plaintext, at: new Date().toISOString() },
          ])
        }
      } catch {}
    }
    return () => ws.close()
  }, [ws])

  const send = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    // Backend expects action: "send_message", content: "<text>"
    wsRef.current.send(JSON.stringify({ action: 'send_message', content: text }))
    setText('')
  }

  return (
    <div className="max-w-2xl mx-auto mt-6 space-y-4 p-4">
      <Card><div className="p-4 font-semibold">Chat with user #{numericId}</div></Card>
      <Card>
        <div className="p-4 space-y-2 max-h-[50vh] overflow-auto">
          {messages.map((m, i) => (
            <div key={i} className="flex items-start gap-2">
              <div className="font-semibold">{m.from}</div>
              <div className="text-gray-800 break-words">{m.text}</div>
              <div className="text-xs text-gray-500 ml-auto">{new Date(m.at).toLocaleTimeString()}</div>
            </div>
          ))}
        </div>
        <div className="p-4 border-t flex gap-2">
          <Input placeholder="Type a message…" value={text} onChange={(e) => setText(e.target.value)} />
          <Button onClick={send}>Send</Button>
        </div>
      </Card>
    </div>
  )
}