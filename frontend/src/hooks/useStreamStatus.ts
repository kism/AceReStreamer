import { useSyncExternalStore } from "react"

export interface StreamStatus {
  hlsStatus: string
  streamURL: string
  videoStats: string
}

let streamStatus: StreamStatus = {
  hlsStatus: "Idle",
  streamURL: "<no stream loaded>",
  videoStats: "",
}

const listeners = new Set<() => void>()

export function updateStreamStatus(newStatus: Partial<StreamStatus>) {
  streamStatus = { ...streamStatus, ...newStatus }
  for (const listener of listeners) {
    listener()
  }
}

export function useStreamStatus() {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
    () => streamStatus,
  )
}
