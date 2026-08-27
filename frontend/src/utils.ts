import useCustomToast from "./hooks/useCustomToast"

// The fetch client is configured with throwOnError, so the thrown value is
// the parsed error body (e.g. FastAPI's {detail: ...}).
export const handleError = (err: unknown) => {
  const { showErrorToast } = useCustomToast()
  const errDetail = (err as { detail?: any })?.detail
  let errorMessage = errDetail || "Something went wrong."
  if (Array.isArray(errDetail) && errDetail.length > 0) {
    errorMessage = errDetail[0].msg
  }
  showErrorToast(errorMessage)
}
