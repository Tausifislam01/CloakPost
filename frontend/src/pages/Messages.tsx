import { useEffect, useState } from 'react'
import Card from '../components/Card'
import Button from '../components/Button'
import Input from '../components/Input'
import { api } from '../lib/api'
import { Link } from 'react-router-dom'

export default function Messages() {
  const [inbox, setInbox] = useState<any[]>([])
  const [to, setTo] = useState('')
  const [text, setText] = useState('')
  const [err, setErr] = useState<string | null>(null)

  const load = async () => {
    try {
      const data = await api.inbox()
      setInbox(data)
    } catch (e: any) {
      setErr(e.message)
    }
  }

  useEffect(() => { load() }, [])

  const send = async () => {
    try {
      await api.sendMessage(to, text)
      setText('')
      await load()
    } catch (e: any) {
      setErr(e.message)
    }
  }

  return (
    <div className="max-w-2xl mx-auto mt-6 space-y-4 p-4">
      <Card>
        <div className="p-4 flex gap-2">
          <Input placeholder="Send to @username" value={to} onChange={(e) => setTo(e.target.value)} />
          <Input placeholder="Message…" value={text} onChange={(e) => setText(e.target.value)} />
          <Button onClick={send}>Send</Button>
        </div>
        {err && <div className="text-red-600 text-sm px-4 pb-3">{err}</div>}
      </Card>

      <Card>
        <div className="p-4">
          <div className="font-semibold mb-2">Inbox</div>
          <div className="space-y-2">
            {inbox.map((row) => (
              <div key={row.username} className="flex items-center justify-between">
                <div>@{row.username} — last: {row.last_message_snippet}</div>
                <Link to={`/chat/${row.username}`} className="text-blue-600 hover:underline">Open chat →</Link>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  )
}
