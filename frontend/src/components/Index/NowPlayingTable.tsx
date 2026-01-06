import { Button, HStack, Table } from "@chakra-ui/react"
import { CopyToClipboard } from "react-copy-to-clipboard-ts"
import { FiCopy } from "react-icons/fi"
import { Code } from "@/components/ui/code"
import { useStreamStatus } from "@/hooks/useVideoPlayer"

export function NowPlayingTable() {
  const streamStatus = useStreamStatus()

  return (
    <Table.Root size="sm" variant="outline">
      <Table.Body>
        <Table.Row>
          <Table.Cell bg="bg.subtle" whiteSpace="nowrap" width="1%" p={2}>
            Player
          </Table.Cell>
          <Table.Cell p={2}>{streamStatus.playerStatus}</Table.Cell>
        </Table.Row>
        <Table.Row>
          <Table.Cell bg="bg.subtle" whiteSpace="nowrap" width="1%" p={2}>
            Stream
          </Table.Cell>
          <Table.Cell p={2}>{streamStatus.hlsStatus}</Table.Cell>
        </Table.Row>
        <Table.Row>
          <Table.Cell bg="bg.subtle" whiteSpace="nowrap" width="1%" p={2}>
            Direct URL
          </Table.Cell>
          <Table.Cell p={2}>
            <HStack>
              <Code>{streamStatus.streamURL}</Code>
              {streamStatus.streamURL.startsWith("http") && (
                <CopyToClipboard text={streamStatus.streamURL}>
                  <Button size="xs">
                    <FiCopy />
                  </Button>
                </CopyToClipboard>
              )}
            </HStack>
          </Table.Cell>
        </Table.Row>
      </Table.Body>
    </Table.Root>
  )
}
