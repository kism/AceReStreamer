import { VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { XtreamCodesService } from "@/client"
import { AppsInfo } from "@/components/info/iptv/AppsInfo"
import { IptvInfo } from "@/components/info/iptv/IptvInfo"
import { usePageTitle } from "@/hooks/usePageTitle"

export const Route = createFileRoute("/_layout/info/iptv")({
  component: InfoIptv,
})

function InfoIptv() {
  usePageTitle("IPTV Info")

  const {
    data: credentials,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["xcCredentials"],
    queryFn: XtreamCodesService.getXcCredentials,
  })

  return (
    <VStack gap={6} align="stretch">
      <IptvInfo
        credentials={credentials || null}
        isLoading={isLoading}
        error={error}
      />
      <AppsInfo />
    </VStack>
  )
}
