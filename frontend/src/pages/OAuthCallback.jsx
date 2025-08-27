import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { setToken } from '../token'
import { API_URL } from '../api'

export default function OAuthCallback() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('Processing login...')

  useEffect(() => {
    const url = new URL(window.location.href)
    const accessToken = url.searchParams.get('access_token')
    const code = url.searchParams.get('code')
    const state = url.searchParams.get('state')
    const error = url.searchParams.get('error')

    const run = async () => {
      try {
        if (error) throw new Error(error)

        if (accessToken) {
          setToken(accessToken)
          navigate('/', { replace: true })
          return
        }

        if (code && state) {
          const resp = await fetch(
            `${API_URL}/auth/google/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`,
            { credentials: 'include' }
          )
          if (!resp.ok) throw new Error(`Callback failed with ${resp.status}`)
          const data = await resp.json()
          if (data?.access_token) {
            setToken(data.access_token)
            navigate('/', { replace: true })
          } else {
            throw new Error('No access_token in response')
          }
          return
        }

        setStatus('Missing parameters in callback URL')
      } catch (e) {
        setStatus(`Login failed: ${e.message || e}`)
      }
    }

    run()
  }, [navigate])

  return (
    <div>
      <h1>OAuth Callback</h1>
      <p>{status}</p>
    </div>
  )
}
