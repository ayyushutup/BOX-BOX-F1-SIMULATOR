const envBase = import.meta.env.VITE_API_BASE_URL?.trim()

const isLocalhost =
  typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')

// In local dev we prefer same-origin paths and let Vite proxy /api -> backend.
const fallbackBase = ''

const sanitizedBase = (envBase || fallbackBase).replace(/\/+$/, '')

export const apiUrl = (path) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  if (sanitizedBase) {
    return `${sanitizedBase}${normalizedPath}`
  }
  if (isLocalhost && normalizedPath.startsWith('/api')) {
    return normalizedPath
  }
  return `${sanitizedBase}${normalizedPath}`
}
