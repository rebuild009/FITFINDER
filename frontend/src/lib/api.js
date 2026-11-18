// Thin client for the FitFinder API. In dev, Vite proxies /api to the FastAPI server.
const BASE = import.meta.env.VITE_API_URL || ''

async function call(path, { method = 'GET', body, signal } = {}) {
  let res
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch (err) {
    if (err.name === 'AbortError') throw err
    throw new Error("Can't reach the FitFinder server. Check that the backend is running on port 8000.", { cause: err })
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const data = await res.json()
      if (typeof data.detail === 'string') detail = data.detail
      else if (Array.isArray(data.detail)) detail = data.detail.map((d) => d.msg).join('; ')
    } catch {
      /* keep the generic message */
    }
    throw new Error(detail)
  }
  return res.json()
}

export const api = {
  meta: () => call('/api/meta'),
  search: (body, signal) => call('/api/search', { method: 'POST', body, signal }),
  match: (body, signal) => call('/api/match', { method: 'POST', body, signal }),
  product: (id, profile, signal) =>
    profile
      ? call(`/api/products/${id}/fit`, { method: 'POST', body: profile, signal })
      : call(`/api/products/${id}`, { signal }),
}
