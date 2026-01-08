import { HStack } from "@chakra-ui/react"
import { Code } from "@/components/ui/code"
import { CopyButton } from "@/components/ui/copy-button"
import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableRow,
  TableRowHeader,
} from "@/components/ui/table"
import { useStreamStatus } from "@/hooks/useVideoPlayer"

function calculateMaxWidth(streamURL: string) {
  const minWidth = 300
  const maxWidth = 1200
  const textWidth = streamURL.length * 11 // Approximate width per character

  if (textWidth < minWidth) {
    return `${minWidth}px`
  }
  if (textWidth > maxWidth) {
    return `${maxWidth}px`
  }
  return `${textWidth}px`
}

export function NowPlayingTable() {
  const streamStatus = useStreamStatus()

  return (
    <AppTableRoot
      preset="outlineSm"
      maxW={calculateMaxWidth(streamStatus.streamURL)}
    >
      <TableBody>
        <TableRow>
          <TableRowHeader>Player</TableRowHeader>
          <TableCell>{streamStatus.playerStatus}</TableCell>
        </TableRow>
        <TableRow>
          <TableRowHeader>Stream</TableRowHeader>
          <TableCell>{streamStatus.hlsStatus}</TableCell>
        </TableRow>
        <TableRow>
          <TableRowHeader>Direct URL</TableRowHeader>
          <TableCell maxWidth={0} minWidth={0}>
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
