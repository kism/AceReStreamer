import { VStack } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { UsersService } from "@/client"
import { AppsInfo, OtherIptvSources } from "@/components/info/AppsInfo"
import { IptvInfo } from "@/components/info/IptvInfo"

async function getUser() {
  const streamTokenService = UsersService.readUserMe()
  return (await streamTokenService) || null
}

export const Route = createFileRoute("/_layout/info/iptv")({
  component: InfoIptv,
  loader: async () => {
    const user = await getUser()
    return { user }
  },
})

function InfoIptv() {
  const { user } = Route.useLoaderData()

  return (
    <VStack gap={6} align="stretch">
      <IptvInfo user={user} />
      <AppsInfo />
      <OtherIptvSources />
    </VStack>
  )
}
