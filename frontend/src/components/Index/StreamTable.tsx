import { Box, EmptyState, Table, VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { FiBarChart, FiSearch } from "react-icons/fi"
import { StreamsService } from "@/client"
import PendingStreams from "@/components/Pending/PendingStreams"
import { loadPlayStream } from "@/hooks/useVideoPlayer"
import { QualityCell } from "./QualityCell"

function getStreamsQueryOptions() {
  return {
    queryFn: () => StreamsService.streams(),
    queryKey: ["items"],
  }
}

export function StreamTable() {
  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getStreamsQueryOptions(),
    placeholderData: (prevData) => prevData,
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const items = data ?? []
  // Sort items by quality descending
  items.sort((a, b) => b.quality - a.quality)

  if (isLoading) {
    return <PendingStreams />
  }

  if (items.length === 0) {
    return (
      <Box>
        <EmptyState.Root>
          <EmptyState.Content>
            <EmptyState.Indicator>
              <FiSearch />
            </EmptyState.Indicator>
            <VStack textAlign="center">
              <EmptyState.Title>No streams found</EmptyState.Title>
              <EmptyState.Description>
                Setup a scraper to find streams.
              </EmptyState.Description>
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
      </Box>
    )
  }

  return (
    <Table.ScrollArea borderWidth="1px" rounded="md" height="100vh">
      <Table.Root size={{ base: "sm", md: "md" }} interactive stickyHeader>
        <Table.Header>
          <Table.Row bg="bg.subtle">
            <Table.ColumnHeader p={2} textAlign="center" width="30px">
              <FiBarChart style={{ margin: "0 auto" }} />
            </Table.ColumnHeader>
            <Table.ColumnHeader p={2} width="90%">
              Stream
            </Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {items?.map((item) => (
            <Table.Row
              key={item.title}
              opacity={isPlaceholderData ? 0.5 : 1}
              cursor={isPlaceholderData ? "default" : "pointer"}
              onClick={() => {
                loadPlayStream(item.content_id)
              }}
            >
              <QualityCell quality={item.quality} p={1} />
              <Table.Cell py={1} px={2} overflow="hidden" maxW="0">
                <Box
                  whiteSpace="nowrap"
                  overflow="hidden"
                  textOverflow="ellipsis"
                >
                  {item.title}
                </Box>
                <Box
                  color="gray.500"
                  whiteSpace="nowrap"
                  overflow="hidden"
                  textOverflow="ellipsis"
                >
                  {item.program_title || "?"}
                </Box>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Table.ScrollArea>
  )
}
