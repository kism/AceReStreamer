import { Box, EmptyState, Text, VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { FiBarChart, FiSearch } from "react-icons/fi"
import { StreamsService } from "@/client"
import PendingStreams from "@/components/Pending/PendingStreams"
import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import baseURL from "@/helpers"
import { QualityCell } from "./QualityCell"

const VITE_API_URL = baseURL()
const loadVideoPlayerModule = () => import("@/hooks/useVideoPlayer")

function getStreamsQueryOptions() {
  return {
    queryFn: () => StreamsService.streams(),
    queryKey: ["items"],
  }
}

function NoStreamsFoundVStack() {
  return (
    <VStack textAlign="center">
      <EmptyState.Title>No streams found</EmptyState.Title>
      <EmptyState.Description>
        Setup a scraper to find streams.
      </EmptyState.Description>
    </VStack>
  )
}

function NoDataVStack() {
  return (
    <VStack textAlign="center">
      <EmptyState.Title>
        <Text color="red.500">Unable to fetch stream list</Text>
      </EmptyState.Title>
    </VStack>
  )
}

export function StreamTable({
  showProgramInformation,
}: {
  showProgramInformation: boolean
}) {
  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getStreamsQueryOptions(),
    placeholderData: (prevData) => prevData,
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const items = data ?? []
  // Sort items by title
  items.sort((a, b) => a.title.localeCompare(b.title))

  if (isLoading) {
    return <PendingStreams />
  }

  if (items.length === 0) {
    return (
      <Box borderWidth="1px" overflow="hidden">
        <AppTableRoot>
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
              {data ? <NoStreamsFoundVStack /> : <NoDataVStack />}
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
      </Box>
    )
  }

  return (
    <Box borderWidth="1px">
      <AppTableRoot m={0}>
        <TableHeader top={0} zIndex={1}>
          {/* Due to sticky header we set bg.subtle */}
          <TableRow bg="bg.subtle">
            <TableColumnHeader maxW="30px">
              <Box display="flex" justifyContent="center">
                <FiBarChart />
              </Box>
            </TableColumnHeader>
            <TableColumnHeader>Stream</TableColumnHeader>
            {showProgramInformation && (
              <TableColumnHeader maxW="150px">Description</TableColumnHeader>
            )}
          </TableRow>
        </TableHeader>
        <TableBody>
          {items?.map((item) => (
            <TableRow
              key={item.stream_url}
              opacity={isPlaceholderData ? 0.5 : 1}
              cursor={isPlaceholderData ? "default" : "pointer"}
              color={
                item.stream_url.endsWith(window.location.hash.substring(1))
                  ? "white"
                  : undefined
              }
              background={
                item.stream_url.endsWith(window.location.hash.substring(1))
                  ? "teal"
                  : undefined
              }
              onClick={() => {
                const relativeUrl = item.stream_url.startsWith(VITE_API_URL)
                  ? item.stream_url.slice(VITE_API_URL.length)
                  : item.stream_url
                loadVideoPlayerModule().then((module) => {
                  module.loadPlayStream(relativeUrl)
                })
              }}
            >
              <QualityCell
                quality={item.quality}
                p={1}
                px={2}
                maxW="30px"
                w="30px"
              />
              {/* This maxW is load bearing */}
              <TableCell overflow="hidden" p={1} maxW={0}>
                <Box
                  whiteSpace="nowrap"
                  overflow="hidden"
                  textOverflow="ellipsis"
                  color="fg"
                >
                  {item.title}
                </Box>
                <Box
                  color={
                    item.stream_url.endsWith(window.location.hash.substring(1))
                      ? "gray.300"
                      : item.program_description
                        ? "fg.muted"
                        : "fg.subtle"
                  }
                  whiteSpace="nowrap"
                  overflow="hidden"
                  textOverflow="ellipsis"
                >
                  {item.program_title || "<No Title>"}
                </Box>
              </TableCell>
              {showProgramInformation && (
                <TableCell textAlign="left" maxW="150px" p={1} px={2}>
                  <Box
                    whiteSpace="normal"
                    overflow="hidden"
                    textOverflow="ellipsis"
                    color={
                      item.stream_url.endsWith(
                        window.location.hash.substring(1),
                      )
                        ? "gray.300"
                        : item.program_description
                          ? undefined
                          : "fg.subtle"
                    }
                  >
                    {item.program_description || "<No Description>"}
                  </Box>
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </AppTableRoot>
    </Box>
  )
}
