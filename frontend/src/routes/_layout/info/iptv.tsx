import { VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { UsersService } from "@/client"
import { AppsInfo, OtherIptvSources } from "@/components/info/iptv/AppsInfo"
import { IptvInfo } from "@/components/info/iptv/IptvInfo"
import { usePageTitle } from "@/hooks/usePageTitle"

export const Route = createFileRoute("/_layout/info/iptv")({
  component: InfoIptv,
})

function InfoIptv() {
  usePageTitle("IPTV Info")

  const {
    data: user,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["currentUser"],
    queryFn: UsersService.readUserMe,
  })

  return (
    <VStack gap={6} align="stretch">
      <IptvInfo user={user || null} isLoading={isLoading} error={error} />
      <AppsInfo />
      <OtherIptvSources />
    </VStack>
  )
}
