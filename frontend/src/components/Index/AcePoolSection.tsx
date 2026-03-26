import { Box, Heading, HStack, Text } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { FiSearch } from "react-icons/fi"
import type { IPTVPoolForAPI } from "@/client"
import { AcePoolService, IptvPoolService } from "@/client"
import { AcePoolBackendInfo } from "@/components/Index/AcePoolBackendInfo"
import { PoolInstancesTable } from "@/components/Index/AcePoolInstancesTable"
import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

function IptvSourcesTable({
  iptvPoolData,
}: { iptvPoolData: IPTVPoolForAPI | undefined }) {
  if (!iptvPoolData?.sources.length) return null

  return (
    <Box>
      <Heading size="sm" py={1}>
        IPTV Proxied Sources
      </Heading>
      <AppTableRoot preset="outlineSm" w="fit-content">
        <TableHeader>
          <TableRow>
            <TableColumnHeader>Source</TableColumnHeader>
            <TableColumnHeader>Streams</TableColumnHeader>
          </TableRow>
        </TableHeader>
        <TableBody>
          {iptvPoolData.sources.map((source) => (
            <TableRow key={source.source_name}>
              <TableCell>{source.source_name}</TableCell>
              <TableCell textAlign="center">
                {source.active_count}/
                {source.max_size === 0 ? "∞" : source.max_size}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </AppTableRoot>
    </Box>
  )
}

export function UpstreamSection() {
  const { isLoading, error, data, isPlaceholderData } = useQuery({
    queryFn: () => AcePoolService.pool(),
    queryKey: ["ace_instances"],
    placeholderData: (prevData) => prevData,
    refetchInterval: 30000,
  })

  const { data: iptvPoolData } = useQuery({
    queryFn: () => IptvPoolService.pool(),
    queryKey: ["iptv_pool"],
    placeholderData: (prevData) => prevData,
    refetchInterval: 30000,
  })

  if (isLoading) {
    return (
      <HStack>
        <FiSearch />
        Fetching acestream information...
      </HStack>
    )
  }

  if (error) {
    return (
      <Box>
        <Text color={"fg.error"}>
          Backend is unavailable:{" "}
          {error instanceof Error ? error.message : String(error)}
        </Text>
      </Box>
    )
  }

  if (!data) {
    return <Text color={"fg.error"}>Unable to fetch Ace Pool info</Text>
  }

  return (
    <>
      <AcePoolBackendInfo
        acePoolData={data}
        isPlaceholderData={isPlaceholderData}
      />
      <IptvSourcesTable iptvPoolData={iptvPoolData} />
      <PoolInstancesTable acePoolData={data} iptvPoolData={iptvPoolData} />
    </>
  )
}
