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
import { useStreamStatus } from "@/hooks/useStreamStatus"

export function NowPlayingTable() {
  const streamStatus = useStreamStatus()

  return (
    <AppTableRoot preset="outlineSm" maxW="600px">
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
          <TableCell maxWidth={0}>
            <HStack gap={2}>
              <Code overflow="hidden" whiteSpace="nowrap" maxWidth="100%">
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
