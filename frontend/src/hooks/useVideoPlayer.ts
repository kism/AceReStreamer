import Hls from "hls.js"
import { useEffect, useState } from "react"

import { UsersService } from "@/client"

import baseURL from "@/helpers"

const VITE_API_URL = baseURL()

const baseHLSURL = `${VITE_API_URL}/hls`
let hls: Hls | null = null

interface StreamStatus {
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

function updateStreamStatus(newStatus: Partial<StreamStatus>) {
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

async function getAuthToken() {
  const streamTokenService = UsersService.readStreamTokenMe()
  return (await streamTokenService)?.stream_token || ""
}

export async function getStreamURL(content_id: string) {
  const token = await getAuthToken()
  return `${baseHLSURL}/${content_id}?token=${token}`
}

export async function loadStream(content_id?: string) {
  const actualContentId = content_id || window.location.hash.substring(1)
  window.location.hash = `#${actualContentId}`

  updateStreamStatus({ playerStatus: "Loading" })
  updateStreamStatus({ hlsStatus: "Initialising" })

  const video = document.querySelector("video") as HTMLVideoElement
  if (!video) {
    console.error("Video element not found")
    return
  }

  if (hls) {
    hls.destroy()
  }

  const streamUrl = await getStreamURL(actualContentId)
  updateStreamStatus({ streamURL: streamUrl })

  if (Hls.isSupported()) {
    hls = new Hls()
    hls.loadSource(streamUrl)
    hls.attachMedia(video)

    updateStreamStatus({ hlsStatus: "Loading" })

    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      updateStreamStatus({ hlsStatus: "Healthy" })
    })

    hls.on(Hls.Events.ERROR, (_event, data) => {
      console.error("HLS error:", data)
      let errorMessage = "Stream loading failed"

      if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
        errorMessage = "Network error: Ace doen't have the stream segment"
      } else if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
        errorMessage = "Media error: Stream not ready"
      } else if (data.type === Hls.ErrorTypes.MUX_ERROR) {
        errorMessage = "Stream parsing error"
      } else if (data.details) {
        errorMessage = `HLS error: ${data.details}`
      }
      updateStreamStatus({ hlsStatus: errorMessage })
    })

    hls.on(Hls.Events.BUFFER_APPENDED, () => {
      updateStreamStatus({ hlsStatus: "Healthy" })
    })
  } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
    // Native HLS support (Safari)
    video.src = streamUrl
    video.addEventListener("loadedmetadata", () => {
      console.log("HLS metadata loaded")
      updateStreamStatus({ hlsStatus: "Loaded" })
    })
  } else {
    console.error("HLS not supported in this browser")
    updateStreamStatus({ hlsStatus: "HLS not supported" })
  }
  return video
}

export async function loadPlayStream(content_id?: string) {
  const actualContentId = content_id || window.location.hash.substring(1)
  window.location.hash = `#${actualContentId}`
  const video = await loadStream(actualContentId)
  video?.play().catch((e) => console.error("Playback failed:", e))
  video?.addEventListener("pause", () =>
    updateStreamStatus({ playerStatus: "Paused" }),
  )
  video?.addEventListener("play", () =>
    updateStreamStatus({ playerStatus: "Playing" }),
  )
}
