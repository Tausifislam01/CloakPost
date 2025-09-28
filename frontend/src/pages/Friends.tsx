import { useEffect, useState } from 'react'
import Card from '../components/Card'
import Input from '../components/Input'
import Button from '../components/Button'
import { api } from '../lib/api'

export default function Friends() {
  const [q, setQ] = useState('')
  const [results, setResults] = useState<string[]>([])
  const [reqs, setReqs] = useState<any[]>([])
  const [err, setErr] = useState<string | null>(null)

  const search = async () => {
    setErr(null)
    try {
      const data = await api.searchUsers(q)
      setResults(data)
    } catch (e: any) {
      setErr(e.message)
    }
  }

  const send = async (u: string) => {
    try {
      await api.sendFriendRequest(u)
      await loadReqs()
    } catch (e: any) {
      setErr(e.message)
    }
  }

  const accept = async (id: number) => {
    try {
      await api.acceptFriendRequest(id)
      await loadReqs()
    } catch (e: any) {
      setErr(e.message)
    }
  }

  const loadReqs = async () => {
    try {
      const data = await api.listFriendRequests()
      setReqs(data)
    } catch (e: any) {
      setErr(e.message)
    }
  }

  useEffect(() => { loadReqs() }, [])

  return (
    <div className="max-w-4xl mx-auto p-4 grid md:grid-cols-2 gap-4">
      <Card>
        <div className="p-4 space-y-3">
          <div className="text-lg font-semibold">Discover</div>
          <div className="flex gap-2">
            <Input placeholder="Search users…" value={q} onChange={(e) => setQ(e.target.value)} />
            <Button onClick={search}>Search</Button>
          </div>
          {err && <div className="text-red-600 text-sm">{err}</div>}
          {results.length > 0 && (
            <div className="space-y-2">
              {results.map((u) => (
                <div key={u} className="flex items-center justify-between px-3 py-2 rounded-xl border">
                  <div className="flex items-center gap-2">
                    <div className="size-8 rounded-full bg-gray-200" />
                    <div>@{u}</div>
                  </div>
                  <Button onClick={() => send(u)} className="bg-white text-gray-900 border hover:bg-gray-50">
                    Add friend
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>

      <Card>
        <div className="p-4 space-y-3">
          <div className="text-lg font-semibold">Requests</div>
          <div className="space-y-2">
            {reqs.map((r: any) => (
              <div key={r.id} className="flex items-center justify-between px-3 py-2 rounded-xl border">
                <div>
                  {r.from_user} ➜ {r.to_user}{' '}
                  <span
                    className={`text-xs ml-2 px-2 py-0.5 rounded-full ${
                      r.status === 'pending' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'
                    }`}
                  >
                    {r.status}
                  </span>
                </div>
                {r.status === 'pending' && <Button onClick={() => accept(r.id)}>Accept</Button>}
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  )
}
