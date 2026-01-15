import { createFileRoute } from "@tanstack/react-router"
import { UsersService } from "@/client"
import { EPGViewer } from "@/components/epg/EPGViewer"
import { usePageTitle } from "@/hooks/usePageTitle"

async function getUser() {
  const streamTokenService = UsersService.readUserMe()
  return (await streamTokenService) || null
}

export const Route = createFileRoute("/_layout/epg")({
  component: EPG,
  loader: async () => {
    const user = await getUser()
    return { user }
  },
})

function EPG() {
  usePageTitle("EPG")
  const { user } = Route.useLoaderData()

  return <EPGViewer user={user} />
}
