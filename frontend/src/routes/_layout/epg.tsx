import { createFileRoute } from "@tanstack/react-router"
import { EPGViewer } from "@/components/epg/EPGViewer"
import { usePageTitle } from "@/hooks/usePageTitle"

export const Route = createFileRoute("/_layout/epg")({
  component: EPG,
})

function EPG() {
  usePageTitle("EPG")

  return <EPGViewer />
}
