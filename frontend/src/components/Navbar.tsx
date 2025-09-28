import { Link, NavLink, useNavigate } from 'react-router-dom'
import Button from './Button'
import { api } from '../lib/api'
import { useSession } from '../context/SessionContext'

export default function Navbar() {
  const nav = useNavigate()
  const { loggedIn, setLoggedIn } = useSession()

  const logout = async () => {
    try { await api.logout() } catch {}
    setLoggedIn(false)
    nav('/login')
  }

  const link = (to: string, label: string) => (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `px-3 py-2 rounded-xl ${isActive ? 'bg-gray-900 text-white' : 'text-gray-700 hover:bg-gray-100'}`
      }
    >
      {label}
    </NavLink>
  )

  return (
    <div className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="font-extrabold text-xl">CloakPost</Link>
        <nav className="hidden md:flex items-center gap-2">
          {link('/', 'Feed')}
          {link('/friends', 'Friends')}
          {link('/messages', 'Messages')}
        </nav>
        <div>
          {loggedIn ? (
            <Button onClick={logout}>Logout</Button>
          ) : (
            <div className="flex gap-2">
              <Link to="/login" className="px-3 py-2">Login</Link>
              <Link to="/register" className="px-3 py-2">Register</Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
