import { Box, Heading, VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { XtreamCodesService } from "@/client"
import { AcePoolSection } from "@/components/Index/AcePoolSection"
import { IptvInfo } from "@/components/info/iptv/IptvInfo"
import { usePageTitle } from "@/hooks/usePageTitle"

export const Route = createFileRoute("/_layout/")({
  component: Info,
})

function Info() {
  usePageTitle("Info")

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
      <VStack gap={6} align="stretch">
        <VStack gap={2} align="stretch">
          <Heading size="md">Status</Heading>
          <AcePoolSection />
        </VStack>
        <VStack gap={2} align="stretch">
          <Heading size="md">IPTV Info</Heading>
          <IptvInfo
            credentials={credentials || null}
            isLoading={isLoading}
            error={error}
          />
        </VStack>
      </VStack>
    </Box>
  )
}
