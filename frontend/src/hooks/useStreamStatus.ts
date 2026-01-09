import { useEffect, useState } from "react"

export interface StreamStatus {
  playerStatus: string
  hlsStatus: string
  streamURL: string
}

let streamStatus: StreamStatus = {
  playerStatus: "Idle",
  hlsStatus: "Idle",
  streamURL: "<no stream loaded>",
}

const statusListeners: Set<(status: StreamStatus) => void> = new Set()

export function updateStreamStatus(newStatus: Partial<StreamStatus>) {
  streamStatus = { ...streamStatus, ...newStatus }
  statusListeners.forEach((listener) => {
    listener(streamStatus)
  })
}

export function useStreamStatus() {
  const [status, setStatus] = useState<StreamStatus>(streamStatus)

  useEffect(() => {
    const listener = (newStatus: StreamStatus) => setStatus(newStatus)
    statusListeners.add(listener)

    return () => {
      statusListeners.delete(listener)
    }
  }, [])

  return status
}
