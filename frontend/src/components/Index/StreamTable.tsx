import { Box, EmptyState, VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { FiBarChart, FiSearch } from "react-icons/fi"
import { StreamsService } from "@/client"
import PendingStreams from "@/components/Pending/PendingStreams"
import {
  AppTableRoot,
  AppTableScrollArea,
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { QualityCell } from "./QualityCell"

const loadVideoPlayerModule = () => import("@/hooks/useVideoPlayer")

function getStreamsQueryOptions() {
  return {
    queryFn: () => StreamsService.streams(),
    queryKey: ["items"],
  }
}

interface StreamTableProps {
  scrollable?: boolean | { base?: boolean; lg?: boolean }
}

export function StreamTable({ scrollable = true }: StreamTableProps) {
  // Handle responsive scrollable prop
  const isScrollableOnBase =
    typeof scrollable === "boolean" ? scrollable : (scrollable.base ?? true)
  const isScrollableOnLg =
    typeof scrollable === "boolean" ? scrollable : (scrollable.lg ?? true)
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
    const content = (
      <>
        <AppTableRoot preset="interactiveSticky">
          <TableHeader>
            {/* Due to sticky header we set bg.subtle */}
            <TableRow bg="bg.subtle">
              <TableColumnHeader width="30px">
                <FiBarChart style={{ margin: "0 auto" }} />
              </TableColumnHeader>
              <TableColumnHeader width="90%">Stream</TableColumnHeader>
            </TableRow>
          </TableHeader>
          <TableBody />
        </AppTableRoot>
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
      </>
    )

    return (
      <>
        {/* Show non-scrollable version on base or lg depending on prop */}
        <Box
          display={{
            base: isScrollableOnBase ? "none" : "block",
            lg: isScrollableOnLg ? "none" : "block",
          }}
          borderWidth="1px"
          borderRadius="md"
          overflow="hidden"
        >
          {content}
        </Box>
        {/* Show scrollable version on base or lg depending on prop */}
        <Box
          display={{
            base: isScrollableOnBase ? "block" : "none",
            lg: isScrollableOnLg ? "block" : "none",
          }}
        >
          <AppTableScrollArea preset="fullscreen">{content}</AppTableScrollArea>
        </Box>
      </>
    )
  }

  const content = (
    <AppTableRoot preset="interactiveSticky">
      <TableHeader>
        {/* Due to sticky header we set bg.subtle */}
        <TableRow bg="bg.subtle">
          <TableColumnHeader width="30px">
            <FiBarChart style={{ margin: "0 auto" }} />
          </TableColumnHeader>
          <TableColumnHeader width="90%">Stream</TableColumnHeader>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items?.map((item) => (
          <TableRow
            key={item.title}
            opacity={isPlaceholderData ? 0.5 : 1}
            cursor={isPlaceholderData ? "default" : "pointer"}
            onClick={() => {
              loadVideoPlayerModule().then((module) => {
                module.loadPlayStream(item.content_id)
              })
            }}
          >
            <QualityCell quality={item.quality} p={1} />
            <TableCell overflow="hidden" maxW="0">
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
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </AppTableRoot>
  )

  return (
    <>
      {/* Show non-scrollable version on base or lg depending on prop */}
      <Box
        display={{
          base: isScrollableOnBase ? "none" : "block",
          lg: isScrollableOnLg ? "none" : "block",
        }}
        borderWidth="1px"
        overflow="hidden"
      >
        {content}
      </Box>
      {/* Show scrollable version on base or lg depending on prop */}
      <Box
        display={{
          base: isScrollableOnBase ? "block" : "none",
          lg: isScrollableOnLg ? "block" : "none",
        }}
        height="100%"
      >
        <AppTableScrollArea preset="fullscreen">{content}</AppTableScrollArea>
      </Box>
    </>
  )
}
