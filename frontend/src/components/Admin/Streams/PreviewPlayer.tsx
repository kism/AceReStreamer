import { AspectRatio, Box, HStack, Text } from "@chakra-ui/react"
import { useEffect, useRef, useState } from "react"
import { FiX } from "react-icons/fi"
import { Button } from "@/components/ui/button"
import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableRow,
} from "@/components/ui/table"
import { setPreviewStream, usePreviewStream } from "@/hooks/usePreviewStream"
import { useStreamStatus } from "@/hooks/useStreamStatus"

// ponytail: shaka stays out of the initial bundle via dynamic import
const loadVideoPlayerModule = () => import("@/hooks/useVideoPlayer")

function StreamStatusTable() {
  const streamStatus = useStreamStatus()

  return (
    <AppTableRoot preset="outlineSm">
      <TableBody>
        <TableRow>
          <TableCell fontWeight="semibold">Stream</TableCell>
          <TableCell>{streamStatus.hlsStatus}</TableCell>
        </TableRow>
        {streamStatus.videoStats && (
          <TableRow>
            <TableCell fontWeight="semibold">Video Stats</TableCell>
            <TableCell>{streamStatus.videoStats}</TableCell>
          </TableRow>
        )}
      </TableBody>
    </AppTableRoot>
  )
}

export function PreviewPlayer() {
  const stream = usePreviewStream()
  const contentId = stream?.content_id
  const panelRef = useRef<HTMLDivElement | null>(null)
  // null = default bottom-right position; set once the user drags
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null)
  const dragOffset = useRef<{ dx: number; dy: number } | null>(null)

  useEffect(() => {
    if (!contentId) return
    let cancelled = false
    loadVideoPlayerModule().then((module) => {
      if (!cancelled) module.loadStream(contentId)
    })
    return () => {
      cancelled = true
      loadVideoPlayerModule().then((module) => module.unloadStream())
    }
  }, [contentId])

  if (!stream) return null

  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    // Pointer capture would retarget the click to this handle, so never start a
    // drag from the close button
    if (e.target instanceof Element && e.target.closest("button")) return
    const rect = panelRef.current?.getBoundingClientRect()
    if (!rect) return
    dragOffset.current = { dx: e.clientX - rect.left, dy: e.clientY - rect.top }
    e.currentTarget.setPointerCapture(e.pointerId)
  }

  const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragOffset.current) return
    const { dx, dy } = dragOffset.current
    setPos({
      x: Math.min(
        Math.max(e.clientX - dx, 0),
        Math.max(window.innerWidth - 100, 0),
      ),
      y: Math.min(
        Math.max(e.clientY - dy, 0),
        Math.max(window.innerHeight - 40, 0),
      ),
    })
  }

  const onPointerUp = () => {
    dragOffset.current = null
  }

  return (
    <Box
      ref={panelRef}
      position="fixed"
      zIndex={1400}
      {...(pos
        ? { left: `${pos.x}px`, top: `${pos.y}px` }
        : { right: "16px", bottom: "16px" })}
      w="400px"
      minW="320px"
      maxW="90vw"
      maxH="95vh"
      bg="bg.panel"
      borderWidth="1px"
      borderRadius="md"
      boxShadow="lg"
      // ponytail: horizontal-only resize keeps height content-driven, so the
      // 16:9 AspectRatio sets it and no dead space can be dragged in
      css={{ resize: "horizontal", overflow: "auto" }}
    >
      <HStack
        px={2}
        py={1}
        bg="bg.muted"
        cursor="move"
        userSelect="none"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
      >
        <Text flex={1} truncate fontWeight="semibold">
          {stream.title}
        </Text>
        <Button
          size="2xs"
          variant="ghost"
          p="0"
          onClick={() => setPreviewStream(null)}
          aria-label="Close preview"
        >
          <FiX />
        </Button>
      </HStack>
      <Box p={2}>
        <AspectRatio w="100%" ratio={16 / 9} mb={2}>
          <div id="shaka-container" style={{ width: "100%", height: "100%" }}>
            <video style={{ width: "100%", height: "100%" }} />
          </div>
        </AspectRatio>
        <StreamStatusTable />
      </Box>
    </Box>
  )
}
