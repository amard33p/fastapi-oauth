import { apiFetch, API_URL } from './api'

export async function loginWithGoogle() {
  const redirectUrl = `${window.location.origin}/oauth-callback`
  const res = await fetch(
    `${API_URL}/auth/google/authorize?redirect_url=${encodeURIComponent(redirectUrl)}`,
    { credentials: 'include' }
  )
  if (!res.ok) {
    throw new Error(`Failed to initiate OAuth: ${res.status}`)
  }
  const data = await res.json()
  if (!data.authorization_url) {
    throw new Error('authorization_url not returned by backend')
  }
  window.location.assign(data.authorization_url)
}

export async function logoutUser() {
  try {
    await fetch(`${API_URL}/auth/cookie/logout`, {
      method: 'POST',
      credentials: 'include',
    })
  } catch (_) {
    // ignore
  }
  window.location.assign('/login')
}

export async function getUser() {
  return apiFetch('/users/me')
}

// No token utilities needed; we rely on HttpOnly cookie
