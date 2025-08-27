import React from 'react'
import { Routes, Route, Link, Navigate, useLocation } from 'react-router-dom'
import Login from './pages/Login'
import Home from './pages/Home'
import OAuthCallback from './pages/OAuthCallback'
import { getToken } from './token'

function RequireAuth({ children }) {
  const token = getToken()
  const location = useLocation()
  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  return children
}

export default function App() {
  return (
    <div style={{ fontFamily: 'system-ui, Arial', padding: 24 }}>
      <nav style={{ marginBottom: 20 }}>
        <Link to="/">Home</Link>{' '}|{' '}
        <Link to="/login">Login</Link>
      </nav>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/oauth-callback" element={<OAuthCallback />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <Home />
            </RequireAuth>
          }
        />
      </Routes>
    </div>
  )
}
