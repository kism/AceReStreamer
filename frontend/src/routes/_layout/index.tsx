import { Box, VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { XtreamCodesService } from "@/client"
import { AcePoolSection } from "@/components/Index/AcePoolSection"
import { IptvInfo } from "@/components/info/iptv/IptvInfo"
import { usePageTitle } from "@/hooks/usePageTitle"

export const Route = createFileRoute("/_layout/")({
  component: Status,
})

function Status() {
  usePageTitle("Status")

  const {
    data: credentials,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["xcCredentials"],
    queryFn: XtreamCodesService.getXcCredentials,
  })

  return (
    <Box maxW="800px">
      <AcePoolSection />
      <VStack gap={6} align="stretch" mt={6}>
        <IptvInfo
          credentials={credentials || null}
          isLoading={isLoading}
          error={error}
        />
      </VStack>
    </Box>
  )
}
