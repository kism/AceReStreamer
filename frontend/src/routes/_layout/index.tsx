import { Box, Flex, Heading, HStack, IconButton } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { lazy, Suspense, useEffect, useState } from "react"
import { FiMaximize2, FiMinimize2, FiRefreshCw } from "react-icons/fi"
import { StreamsService } from "@/client"
import { AcePoolInfo } from "@/components/Index/AcePoolInfo"
import { NowPlayingTable } from "@/components/Index/NowPlayingTable"
import { StreamTable } from "@/components/Index/StreamTable"
import { usePageTitle } from "@/hooks/usePageTitle"

const VideoPlayer = lazy(() =>
  import("@/components/Index/VideoPlayer").then((module) => ({
    default: module.VideoPlayer,
  })),
)

// Lazy load video player functions to avoid loading hls.js on initial page load
const loadVideoPlayerModule = () => import("@/hooks/useVideoPlayer")

export const Route = createFileRoute("/_layout/")({
  component: WebPlayer,
})

function WebPlayer() {
  const [isExpanded, setIsExpanded] = useState(false)
  const [contentId, setContentId] = useState(window.location.hash.substring(1))

  useEffect(() => {
    const handleHashChange = () => {
      setContentId(window.location.hash.substring(1))
    }

    window.addEventListener("hashchange", handleHashChange)
    return () => window.removeEventListener("hashchange", handleHashChange)
  }, [])

  const { data: streamData } = useQuery({
    queryFn: () => StreamsService.byContentId({ contentId }),
    queryKey: ["content_id", contentId],
    placeholderData: (prevData) => prevData,
    enabled: !!contentId,
  })
  usePageTitle(streamData?.title || "Home")

  useEffect(() => {
    if (window.location.hash) {
      loadVideoPlayerModule().then((module) => {
        module.loadStream(window.location.hash.substring(1))
      })
    }
  }, []) // Run once on mount

  return (
    <Flex
      height="100%"
      gap={2}
      direction={{ base: "column", lg: isExpanded ? "column" : "row" }}
    >
      {/* Left pane - Video Player */}
      <Flex direction="column" flex="1" minW="0" gap={2}>
        <Box>
          <Heading size="sm">
            {streamData?.program_title
              ? streamData.program_title
              : "No Program Information"}
          </Heading>
        </Box>
        <Suspense
          fallback={
            <Box
              w="100%"
              aspectRatio={16 / 9}
              bg="gray.800"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              Loading player...
            </Box>
          }
        >
          <VideoPlayer />
        </Suspense>
        <HStack>
          <IconButton
            aria-label="Reload stream"
            size="2xs"
            p={2}
            fontWeight={"normal"}
            onClick={() => {
              const currentStreamId = window.location.hash.substring(1)
              if (currentStreamId) {
                loadVideoPlayerModule().then((module) => {
                  module.loadPlayStream(currentStreamId)
                })
              }
            }}
          >
            <FiRefreshCw />
            Reload
          </IconButton>
          <IconButton
            aria-label={isExpanded ? "Restore layout" : "Expand video player"}
            size="2xs"
            p={2}
            fontWeight={"normal"}
            display={{ base: "none", lg: "flex" }}
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? <FiMinimize2 /> : <FiMaximize2 />}
            {isExpanded ? "Restore Layout" : "Expand Player"}
          </IconButton>
        </HStack>

        <NowPlayingTable />
        <AcePoolInfo />
      </Flex>

      {/* Right pane - Items Table */}
      <Flex
        direction="column"
        flex={{ base: "0 0 auto", lg: "1" }}
        maxW={{ base: "100%", lg: isExpanded ? "100%" : "300px" }}
        minW="200px"
      >
        <StreamTable />
      </Flex>
    </Flex>
  )
}
