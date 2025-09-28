import { useEffect, useState } from 'react'
import Card from '../components/Card'
import Button from '../components/Button'
import Input from '../components/Input'
import { api } from '../lib/api'
import { Post } from '../../types'

export default function Feed() {
  const [posts, setPosts] = useState<Post[]>([])
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const load = async () => {
    try {
      const data = await api.listPosts()
      setPosts(data)
    } catch (e: any) {
      setErr(e.message)
    }
  }

  useEffect(() => { load() }, [])

  const create = async () => {
    setLoading(true)
    setErr(null)
    try {
      await api.createPost(text)
      setText('')
      await load()
    } catch (e: any) {
      setErr(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-4 space-y-4">
      <Card>
        <div className="p-4">
          <div className="flex gap-3">
            <Input
              placeholder="Write something encrypted…"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <Button onClick={create} loading={loading}>
              Post
            </Button>
          </div>
          {err && <div className="text-red-600 text-sm mt-2">{err}</div>}
        </div>
      </Card>

      {posts.map((p) => (
        <Card key={p.id}>
          <div className="p-4">
            <div className="flex items-center justify-between text-sm text-gray-500">
              <div className="font-medium text-gray-700">@{p.author}</div>
              <div>{new Date(p.created_at).toLocaleString()}</div>
            </div>
            <div className="mt-2 flex items-start gap-2">
              <div className="mt-0.5">🔒</div>
              <div className="font-mono break-words text-gray-800">{p.ciphertext}</div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  )
}
