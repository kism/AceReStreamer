import { Box, Heading, HStack, Text, VStack } from "@chakra-ui/react"
import { Code } from "@/components/ui/code"
import { CopyButton } from "@/components/ui/copy-button"
import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableRow,
} from "@/components/ui/table"
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
        <Heading>Xtream IPTV</Heading>
        <Text>
          Add a playlist/source with your IPTV app, use the XC/Xtream setting
          when adding. EPG should work automatically. If its not available,
          follow the regular IPTV instructions.
        </Text>
        <AppTableRoot preset="outlineSm" my={2}>
          <TableBody>
            {[
              { name: "Server/Portal URL", value: serverAddress },
              { name: "Username", value: username },
              { name: "Password", value: password },
            ].map(({ name, value }) => (
              <TableRow key={name}>
                <TableCell bg="bg.subtle" whiteSpace="nowrap" width="1%">
                  {name}
                </TableCell>
                <TableCell>
                  <HStack>
                    <Code>{value}</Code>
                    <CopyButton text={value} />
                  </HStack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </AppTableRoot>
        <Text>If authentication is disabled, any value will work.</Text>
      </Box>

      <Box>
        <Heading>IPTV</Heading>
        <Text>
          Depending on the app, you might need to use an alternate Playlist or
          EPG url.
        </Text>
        <Text>Some apps will only work if this site is on https.</Text>
        <AppTableRoot preset="outlineSm" my={2}>
          <TableBody>
            {[
              { name: "Playlist URL", url: playlistUrl },
              { name: "Playlist URL (.m3u)", url: playlistM3uUrl },
              { name: "Playlist URL (.m3u8)", url: playlistM3u8Url },
              { name: "EPG URL", url: epgUrl },
              { name: "EPG URL (.xml)", url: epgXmlUrl },
            ].map(({ name, url }) => (
              <TableRow key={name}>
                <TableCell bg="bg.subtle" whiteSpace="nowrap" width="1%">
                  {name}
                </TableCell>
                <TableCell>
                  <HStack>
                    <Code>{url}</Code>
                    <CopyButton text={url} />
                  </HStack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </AppTableRoot>
      </Box>
    </VStack>
  )
}
