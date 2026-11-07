// Thin client for the backend API (proxied under /api, see vite.config.js).
const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let message = `HTTP ${res.status}`
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') message = body.detail
    } catch {
      // response had no JSON body
    }
    throw new Error(message)
  }
  return res.status === 204 ? null : res.json()
}

export const listLocations = () => request('/locations/')

export const createLocation = (data) =>
  request('/locations/', { method: 'POST', body: JSON.stringify(data) })

export const deleteLocation = (id) =>
  request(`/locations/${id}`, { method: 'DELETE' })
