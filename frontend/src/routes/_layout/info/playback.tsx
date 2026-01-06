import { createFileRoute } from "@tanstack/react-router"
import { PlaybackInfo } from "@/components/info/PlaybackInfo"

export const Route = createFileRoute("/_layout/info/playback")({
  component: InfoDesktop,
})

function InfoDesktop() {
  return <PlaybackInfo />
}
