import { AspectRatio, HStack } from "@chakra-ui/react"
import { useEffect } from "react"
import type { FoundAceStreamAPI } from "@/client"
import { Code } from "@/components/ui/code"
import { CopyButton } from "@/components/ui/copy-button"
import {
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableRow,
} from "@/components/ui/table"
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
        <TableRow>
          <TableCell fontWeight="semibold">Direct URL</TableCell>
          <TableCell maxWidth={0}>
            <HStack gap={2} minWidth={0}>
              <Code
                overflowX="auto"
                whiteSpace="nowrap"
                display="block"
                flex={1}
                minWidth={0}
              >
                {streamStatus.streamURL}
              </Code>
              {streamStatus.streamURL.startsWith("http") && (
                <CopyButton text={streamStatus.streamURL} />
              )}
            </HStack>
          </TableCell>
        </TableRow>
      </TableBody>
    </AppTableRoot>
  )
}

interface PreviewDialogProps {
  stream: FoundAceStreamAPI | null
  onClose: () => void
}

export function PreviewDialog({ stream, onClose }: PreviewDialogProps) {
  const contentId = stream?.content_id

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

  return (
    <DialogRoot
      open={stream !== null}
      onOpenChange={(e) => {
        if (!e.open) onClose()
      }}
      size="xl"
    >
      <DialogContent
        css={{ resize: "horizontal", overflow: "auto" }}
        minW="320px"
        maxW="90vw"
      >
        <DialogHeader>
          <DialogTitle>{stream?.title}</DialogTitle>
        </DialogHeader>
        <DialogCloseTrigger />
        <DialogBody>
          <AspectRatio w="100%" ratio={16 / 9} mb={2}>
            <div id="shaka-container" style={{ width: "100%", height: "100%" }}>
              <video style={{ width: "100%", height: "100%" }} />
            </div>
          </AspectRatio>
          <StreamStatusTable />
        </DialogBody>
      </DialogContent>
    </DialogRoot>
  )
}
