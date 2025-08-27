import React, { useEffect, useState } from 'react'
import { loginWithGoogle, getUser } from '../authClient'
import { Link } from 'react-router-dom'

export default function Login() {
  const [loggedIn, setLoggedIn] = useState(null)

  useEffect(() => {
    let mounted = true
    getUser()
      .then(() => mounted && setLoggedIn(true))
      .catch(() => mounted && setLoggedIn(false))
    return () => {
      mounted = false
    }
  }, [])

  return (
    <div>
      <h1>Login</h1>
      {loggedIn === null ? (
        <p>Checking your session…</p>
      ) : loggedIn ? (
        <p>
          You are already logged in. Go to <Link to="/">Home</Link>.
        </p>
      ) : (
        <button onClick={loginWithGoogle}>Login with Google</button>
      )}
    </div>
  )
}
