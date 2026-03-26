import shaka from "shaka-player/dist/shaka-player.ui"
import "shaka-player/dist/controls.css"
import "./videoPlayer.css"

import { UsersService } from "@/client"
import { baseUrl } from "@/helpers"

import { updateStreamStatus } from "./useStreamStatus"

let overlay: shaka.ui.Overlay | null = null
let player: shaka.Player | null = null
let cachedToken: string | null = null
let statsInterval: ReturnType<typeof setInterval> | null = null

function startStatsPolling() {
  stopStatsPolling()
  statsInterval = setInterval(() => {
    if (!player) return
    const tracks = player.getVariantTracks()
    const active = tracks.find((t) => t.active)
    if (active) {
      const parts: string[] = []
      if (active.width && active.height)
        parts.push(`${active.width}x${active.height}`)
      if (active.videoCodec) parts.push(active.videoCodec)
      if (active.audioCodec) parts.push(active.audioCodec)
      updateStreamStatus({ videoStats: parts.join(" / ") })
    }
  }, 2000)
}

function stopStatsPolling() {
  if (statsInterval) {
    clearInterval(statsInterval)
    statsInterval = null
  }
}

async function getAuthToken() {
  if (cachedToken !== null) {
    return cachedToken
  }
  const result = await UsersService.readStreamTokenMe()
  cachedToken = result?.stream_token || ""
  return cachedToken
}

export async function getStreamURL(streamUrl: string) {
  const token = await getAuthToken()
  const resolvedUrl = streamUrl.startsWith("/")
    ? `${baseUrl()}${streamUrl}`
    : streamUrl
  const separator = resolvedUrl.includes("?") ? "&" : "?"
  return `${resolvedUrl}${separator}token=${token}`
}

export async function loadStream(streamUrl?: string) {
  const actualStreamUrl = streamUrl || window.location.hash.substring(1)
  window.location.hash = `#${actualStreamUrl}`

  updateStreamStatus({
    hlsStatus: "Initialising",
    videoStats: "",
  })
  stopStatsPolling()

  const container = document.getElementById(
    "shaka-container",
  ) as HTMLElement | null
  const video = container?.querySelector("video") as HTMLVideoElement | null
  if (!container || !video) {
    console.error("Video container or element not found")
    return
  }

  if (overlay) {
    stopStatsPolling()
    await overlay.destroy()
    overlay = null
    player = null
  }

  // Clean up any residual Shaka UI elements left after destroy
  if (video.parentElement !== container) {
    container.appendChild(video)
  }
  for (const child of Array.from(container.children)) {
    if (child !== video) {
      child.remove()
    }
  }

  const fullUrl = await getStreamURL(actualStreamUrl)
  updateStreamStatus({ streamURL: fullUrl })

  if (shaka.Player.isBrowserSupported()) {
    player = new shaka.Player()
    await player.attach(video)
    overlay = new shaka.ui.Overlay(player, container, video)

    overlay.configure({
      forceLandscapeOnFullscreen: true,
      seekBarColors: {
        played: "#008080",
        buffered: "rgba(0, 128, 128, 0.4)",
        base: "rgba(255, 255, 255, 0.3)",
      },
      controlPanelElements: [
        // No cog for settings
        "play_pause",
        "mute",
        "volume",
        "time_and_duration",
        "spacer",
        "fullscreen",
      ],
    })

    // We don't have much faith in IPTV or Acestream so we play it safe.
    player.configure({
      streaming: {
        lowLatencyMode: false,
        rebufferingGoal: 15,
        bufferingGoal: 30,
        bufferBehind: 60,
        loadTimeout: 60,
        stopFetchingOnPause: false,
        retryParameters: {
          maxAttempts: 10,
          baseDelay: 1000,
          backoffFactor: 2,
          fuzzFactor: 0.5,
        },
      },
    })

    player.addEventListener("error", (event) => {
      const detail = (event as unknown as { detail: shaka.util.Error }).detail
      console.error("Shaka error:", detail)

      let errorMessage = "Stream loading failed"
      if (detail.category === shaka.util.Error.Category.NETWORK) {
        errorMessage = "Network error: Ace doesn't have the stream segment"
      } else if (detail.category === shaka.util.Error.Category.MEDIA) {
        errorMessage = "Media error: Stream not ready"
      } else if (detail.message) {
        errorMessage = `Player error: ${detail.message}`
      }
      updateStreamStatus({ hlsStatus: errorMessage })
    })

    player.addEventListener("buffering", (event) => {
      const buffering = (event as unknown as { buffering: boolean }).buffering
      if (!buffering) {
        updateStreamStatus({ hlsStatus: "Healthy" })
      }
    })

    updateStreamStatus({ hlsStatus: "Loading" })

    try {
      await player.load(fullUrl)
      updateStreamStatus({ hlsStatus: "Healthy" })
      startStatsPolling()
      video.play()
    } catch (e) {
      if (e instanceof shaka.util.Error) {
        console.error("Shaka load error:", e)
        updateStreamStatus({ hlsStatus: `Load error: ${e.message}` })
      } else {
        throw e
      }
    }
  } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
    // Native HLS support (Safari)
    video.src = fullUrl
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

export async function loadPlayStream(streamUrl?: string) {
  const actualStreamUrl = streamUrl || window.location.hash.substring(1)
  window.location.hash = `#${actualStreamUrl}`
  const video = await loadStream(actualStreamUrl)
  video?.play().catch((e) => console.error("Playback failed:", e))
}
