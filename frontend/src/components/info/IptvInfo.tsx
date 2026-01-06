import {
  Box,
  Button,
  Heading,
  HStack,
  Table,
  Text,
  VStack,
} from "@chakra-ui/react"
import { CopyToClipboard } from "react-copy-to-clipboard-ts"
import { FiCopy } from "react-icons/fi"
import { Code } from "@/components/ui/code"
import baseURL from "@/helpers"

const VITE_API_URL = baseURL()

interface IptvInfoProps {
  user: {
    username?: string
    stream_token?: string
  } | null
}

export function IptvInfo({ user }: IptvInfoProps) {
  const tokenString = user?.stream_token ? `?token=${user.stream_token}` : ""

  const serverAddress = VITE_API_URL
  const username = user?.username || "any"
  const password = user?.stream_token || "any"
  const playlistUrl = `${VITE_API_URL}/iptv${tokenString}`
  const playlistM3uUrl = `${VITE_API_URL}/iptv.m3u${tokenString}`
  const playlistM3u8Url = `${VITE_API_URL}/iptv.m3u8${tokenString}`
  const epgUrl = `${VITE_API_URL}/epg${tokenString}`
  const epgXmlUrl = `${VITE_API_URL}/epg.xml${tokenString}`

  return (
    <VStack gap={6} align="stretch">
      <Box>
        <Heading size="lg">Xtream IPTV</Heading>
        <Text>
          Add a playlist/source with your IPTV app, use the XC/Xtream setting
          when adding. EPG should work automatically. If its not available,
          follow the regular IPTV instructions.
        </Text>
        <Table.Root my={2} size="sm" variant="outline">
          <Table.Body>
            {[
              { name: "Server/Portal URL", value: serverAddress },
              { name: "Username", value: username },
              { name: "Password", value: password },
            ].map(({ name, value }) => (
              <Table.Row key={name}>
                <Table.Cell bg="bg.subtle" whiteSpace="nowrap" width="1%">
                  {name}
                </Table.Cell>
                <Table.Cell>
                  <HStack>
                    <Code>{value}</Code>
                    <CopyToClipboard text={value}>
                      <Button size="xs">
                        <FiCopy />
                      </Button>
                    </CopyToClipboard>
                  </HStack>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
        <Text>If authentication is disabled, any value will work.</Text>
      </Box>

      <Box>
        <Heading size="lg">IPTV</Heading>
        <Text>
          Depending on the app, you might need to use an alternate Playlist or
          EPG url.
        </Text>
        <Text>Some apps will only work if this site is on https.</Text>
        <Table.Root my={2} size="sm" variant="outline">
          <Table.Body>
            {[
              { name: "Playlist URL", url: playlistUrl },
              { name: "Playlist URL (.m3u)", url: playlistM3uUrl },
              { name: "Playlist URL (.m3u8)", url: playlistM3u8Url },
              { name: "EPG URL", url: epgUrl },
              { name: "EPG URL (.xml)", url: epgXmlUrl },
            ].map(({ name, url }) => (
              <Table.Row key={name}>
                <Table.Cell bg="bg.subtle" whiteSpace="nowrap" width="1%">
                  {name}
                </Table.Cell>
                <Table.Cell>
                  <HStack>
                    <Code>{url}</Code>
                    <CopyToClipboard text={url}>
                      <Button size="xs">
                        <FiCopy />
                      </Button>
                    </CopyToClipboard>
                  </HStack>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      </Box>
    </VStack>
  )
}
