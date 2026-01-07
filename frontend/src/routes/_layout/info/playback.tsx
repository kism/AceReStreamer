import { createFileRoute } from "@tanstack/react-router"
import { PlaybackInfo } from "@/components/info/PlaybackInfo"
import { usePageTitle } from "@/hooks/usePageTitle"

export const Route = createFileRoute("/_layout/info/playback")({
  component: InfoDesktop,
})

function InfoDesktop() {
  usePageTitle("Playback Info")
  return <PlaybackInfo />
}
