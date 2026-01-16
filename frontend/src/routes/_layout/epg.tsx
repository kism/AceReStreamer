import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { UsersService } from "@/client"
import { EPGViewer } from "@/components/epg/EPGViewer"
import { usePageTitle } from "@/hooks/usePageTitle"

export const Route = createFileRoute("/_layout/epg")({
  component: EPG,
})

function EPG() {
  usePageTitle("EPG")

  const { data: user } = useQuery({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
  })

  return <EPGViewer user={user || null} />
}
