import { FormEvent, useState } from 'react'
import Card from '../components/Card'
import Input from '../components/Input'
import Button from '../components/Button'
import { api } from '../lib/api'
import { useNavigate } from 'react-router-dom'
import { useSession } from '../context/SessionContext'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const nav = useNavigate()
  const { setLoggedIn } = useSession()

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await api.login(username, password)
      setLoggedIn(true)
      nav('/')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto mt-10">
      <Card>
        <div className="p-4">
          <h1 className="text-2xl font-semibold mb-4">Login</h1>
          <form onSubmit={onSubmit} className="space-y-3">
            <Input
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            {error && <div className="text-red-600 text-sm">{error}</div>}
            <Button loading={loading} type="submit" className="w-full">
              Login
            </Button>
          </form>
        </div>
      </Card>
    </div>
  )
}
