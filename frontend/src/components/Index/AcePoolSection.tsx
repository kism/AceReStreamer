import { Box, HStack, Text } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { FiSearch } from "react-icons/fi"
import { AcePoolService } from "@/client"
import { AcePoolBackendInfo } from "@/components/Index/AcePoolBackendInfo"
import { AcePoolInstancesTable } from "@/components/Index/AcePoolInstancesTable"
import { STATUS_COLORS } from "@/components/Index/constants"

export function AcePoolSection() {
  const { isLoading, error, data, isPlaceholderData } = useQuery({
    queryFn: () => AcePoolService.pool(),
    queryKey: ["ace_instances"],
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
        <Text color={STATUS_COLORS.error}>
          Backend is unavailable:{" "}
          {error instanceof Error ? error.message : String(error)}
        </Text>
      </Box>
    )
  }

  if (!data) {
    return (
      <Text color={STATUS_COLORS.error}>Unable to fetch Ace Pool info</Text>
    )
  }

  return (
    <>
      <AcePoolBackendInfo
        acePoolData={data}
        isPlaceholderData={isPlaceholderData}
      />
      <AcePoolInstancesTable acePoolData={data} />
    </>
  )
}
