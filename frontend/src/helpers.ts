const _VITE_API_URL = import.meta.env.VITE_API_URL

export function baseUrl() {
  if (!_VITE_API_URL) {
    return ""
  }
  return _VITE_API_URL
}

export default baseUrl
