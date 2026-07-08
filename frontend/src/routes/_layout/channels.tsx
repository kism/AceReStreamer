import { createFileRoute } from "@tanstack/react-router"
import StreamManagement from "@/components/Admin/StreamManagement"
import { usePageTitle } from "@/hooks/usePageTitle"

export const Route = createFileRoute("/_layout/channels")({
  component: Channels,
})

function Channels() {
  usePageTitle("Channels")

  return <StreamManagement />
}
