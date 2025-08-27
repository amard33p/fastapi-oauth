import React, { useState } from 'react'
import Auth from '../Auth.jsx'
import { apiFetch } from '../api'

export default function Home() {
  const [message, setMessage] = useState('')

  const callProtected = async () => {
    try {
      const data = await apiFetch('/authenticated-route')
      setMessage(JSON.stringify(data))
    } catch (e) {
      setMessage(String(e))
    }
  }

  return (
    <div>
      <h1>Home</h1>
      <Auth />
      <div style={{ marginTop: 16 }}>
        <button onClick={callProtected}>Call /authenticated-route</button>
        {message && (
          <pre style={{ background: '#f7f7f7', padding: 12, marginTop: 12 }}>{message}</pre>
        )}
      </div>
    </div>
  )
}
