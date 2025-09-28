import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Feed from './pages/Feed'
import Friends from './pages/Friends'
import Messages from './pages/Messages'
import Chat from './pages/Chat'
import Login from './pages/Login'
import Register from './pages/Register'
import { SessionProvider, useSession } from './context/SessionContext'
import './styles.css'

function RequireAuth({ children }: { children: JSX.Element }) {
  const { loggedIn } = useSession()
  if (!loggedIn) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <SessionProvider>
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/" element={<RequireAuth><Feed /></RequireAuth>} />
          <Route path="/friends" element={<RequireAuth><Friends /></RequireAuth>} />
          <Route path="/messages" element={<RequireAuth><Messages /></RequireAuth>} />
          <Route path="/chat/:peerId" element={<RequireAuth><Chat /></RequireAuth>} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Routes>
      </BrowserRouter>
    </SessionProvider>
  )
}
