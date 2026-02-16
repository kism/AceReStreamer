function stripTrailingSlashes(value: string) {
  return value.replace(/\/+$/, "")
}

export function baseUrl() {
  const configured = (import.meta.env.VITE_API_URL ?? "").trim()
  if (configured) {
    return stripTrailingSlashes(configured)
  }

  if (typeof window !== "undefined" && window?.location?.origin) {
    return window.location.origin
  }

  return ""
}

export default baseUrl
