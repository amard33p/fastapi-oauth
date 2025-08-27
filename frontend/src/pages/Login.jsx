import React from 'react'
import { loginWithGoogle } from '../authClient'
import { getToken } from '../token'
import { Link } from 'react-router-dom'

export default function Login() {
  const token = getToken()
  return (
    <div>
      <h1>Login</h1>
      {token ? (
        <p>
          You are already logged in. Go to <Link to="/">Home</Link>.
        </p>
      ) : (
        <button onClick={loginWithGoogle}>Login with Google</button>
      )}
    </div>
  )
}
