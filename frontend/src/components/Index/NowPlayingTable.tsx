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
export function NowPlayingTable() {
  const streamStatus = useStreamStatus()

  return (
    <AppTableRoot preset="outlineSm" width="100%">
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
          <TableCell maxW={0}>
            <HStack gap={2} minWidth={0}>
              <Code
                overflowWrap="anywhere"
                wordBreak="break-all"
                whiteSpace="normal"
                display="block"
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
