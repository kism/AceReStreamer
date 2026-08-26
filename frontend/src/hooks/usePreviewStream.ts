import { useSyncExternalStore } from "react"
import type { FoundAceStreamAPI } from "@/client"

// Module-level store so the preview player survives route navigation,
// same pattern as useStreamStatus.
let previewStream: FoundAceStreamAPI | null = null
const listeners = new Set<() => void>()

export function setPreviewStream(stream: FoundAceStreamAPI | null) {
  previewStream = stream
  for (const listener of listeners) {
    listener()
  }
}

export function usePreviewStream() {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
    () => previewStream,
  )
}
