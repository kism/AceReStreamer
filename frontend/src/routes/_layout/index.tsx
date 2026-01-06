import { Flex } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { useEffect } from "react"
import { AcePoolInfo } from "@/components/Index/AcePoolInfo"
import { DynamicTitle } from "@/components/Index/DynamicTitle"
import { NowPlayingTable } from "@/components/Index/NowPlayingTable"
import { StreamTable } from "@/components/Index/StreamTable"
import { VideoPlayer } from "@/components/Index/VideoPlayer"
import { loadStream } from "@/hooks/useVideoPlayer"

export const Route = createFileRoute("/_layout/")({
  component: WebPlayer,
})

function WebPlayer() {
  useEffect(() => {
    if (window.location.hash) {
      loadStream(window.location.hash.substring(1))
    }
  }, []) // Run once on mount

  return (
    <Flex height="100%" gap={4} direction={{ base: "column", lg: "row" }}>
      {/* Left pane - Video Player */}
      <Flex direction="column" flex="1" minW="0" gap={4}>
        <DynamicTitle />
        <VideoPlayer />
        <NowPlayingTable />
        <AcePoolInfo />
      </Flex>

      {/* Right pane - Items Table */}
      <Flex
        direction="column"
        flex={{ base: "1", lg: "1" }}
        maxW={{ base: "100%", lg: "400px" }}
        minW="200px"
      >
        <StreamTable />
      </Flex>
    </Flex>
  )
}
