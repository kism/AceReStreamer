import {
  Box,
  Flex,
  Heading,
  HStack,
  IconButton,
  Text,
  useBreakpointValue,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import { FiMaximize2, FiMinimize2, FiRefreshCw } from "react-icons/fi"
import { StreamsService } from "@/client"
import { UpstreamSection } from "@/components/Index/AcePoolSection"
import { NowPlayingTable } from "@/components/Index/NowPlayingTable"
import { StreamTable } from "@/components/Index/StreamTable"
import { VideoPlayer } from "@/components/Index/VideoPlayer"
import { usePageTitle } from "@/hooks/usePageTitle"

// Dynamic import for shaka-player module - preloaded after render, instantly available on click
const loadVideoPlayerModule = () => import("@/hooks/useVideoPlayer")

// Preload shaka-player in the background after the page is idle
if (typeof window !== "undefined") {
  const preload = () => loadVideoPlayerModule()
  if ("requestIdleCallback" in window) {
    window.requestIdleCallback(preload)
  } else {
    setTimeout(preload, 200)
  }
}

export const Route = createFileRoute("/_layout/")({
  component: WebPlayer,
})

function ProgramDescription({
  description,
  title,
}: {
  description?: string
  title?: string
}) {
  if (!title) return null

  return (
    <Box>
      <Heading size="sm" py={1}>
        <HStack>
          <Text>Now Playing: </Text> {title ? title : "No Program Information"}
        </HStack>
      </Heading>
      <Text borderWidth="1px" px={2} py={1} maxW="600px">
        {description ? description : "No Program Description Available"}
      </Text>
    </Box>
  )
}

function PlayerControls({
  isExpanded,
  onToggleExpand,
}: {
  isExpanded: boolean
  onToggleExpand: () => void
}) {
  return (
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
        onClick={onToggleExpand}
      >
        {isExpanded ? <FiMinimize2 /> : <FiMaximize2 />}
        {isExpanded ? "Restore Layout" : "Expand Player"}
      </IconButton>
    </HStack>
  )
}

function WebPlayer() {
  const [isExpanded, setIsExpanded] = useState(false)
  const [streamUrl, setStreamUrl] = useState(window.location.hash.substring(1))
  const isLarge = useBreakpointValue({ base: false, lg: true })
  const isSmall = useBreakpointValue({
    base: true,
    sm: true,
    md: false,
    lg: false,
  })

  // Show program info when layout is vertical (sidebar not on side)
  const showProgramInformation = (!isLarge || isExpanded) && !isSmall

  useEffect(() => {
    const handleHashChange = () => {
      setStreamUrl(window.location.hash.substring(1))
    }

    window.addEventListener("hashchange", handleHashChange)
    return () => window.removeEventListener("hashchange", handleHashChange)
  }, [])

  const { data: allStreams } = useQuery({
    queryFn: () => StreamsService.streams(),
    queryKey: ["items"],
    placeholderData: (prevData) => prevData,
  })
  const streamData = allStreams?.find((s) => s.stream_url === streamUrl)
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
        <VideoPlayer />
        <PlayerControls
          isExpanded={isExpanded}
          onToggleExpand={() => setIsExpanded(!isExpanded)}
        />
        <VStack align="stretch" gap={4}>
          <NowPlayingTable />
          <ProgramDescription
            description={streamData?.program_description ?? ""}
            title={streamData?.program_title ?? ""}
          />
          <UpstreamSection />
          <Box flexShrink={0} h={4} /> {/* Bit of a hack */}
        </VStack>
      </Flex>

      {/* Right pane - Streams Table */}
      <Flex
        direction="column"
        flex={{ base: "0 0 auto", lg: "1" }}
        maxW={{ base: "100%", lg: isExpanded ? "100%" : "300px" }}
        minW="200px"
        overflow="visible"
        pb={{ base: 10, lg: 4 }} // Overscroll is nice on mobile
      >
        <StreamTable showProgramInformation={showProgramInformation} />
        <Box flexShrink={0} h={4} /> {/* Bit of a hack */}
      </Flex>
    </Flex>
  )
}
