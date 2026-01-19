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
  isLoading: boolean
  error: Error | null
}

function renderTableRows(items: Array<{ name: string; value: string }>) {
  return items.map(({ name, value }) => (
    <TableRow key={name}>
      <TableCell
        bg="bg.subtle"
        width="1%"
        whiteSpace={{ base: "wrap", md: "nowrap" }}
      >
        {name}
      </TableCell>
      <TableCell maxWidth={0}>
        <HStack minWidth={0}>
          <Code
            overflowX="auto"
            whiteSpace="nowrap"
            display="block"
            flex={1}
            minWidth={0}
          >
            {value}
          </Code>
          <CopyButton text={value} />
        </HStack>
      </TableCell>
    </TableRow>
  ))
}

export function IptvInfo({ user, isLoading, error }: IptvInfoProps) {
  if (isLoading) return <Text>Loading...</Text>
  if (error)
    return (
      <Text color="red">Cannot Load IPTV information: {error.message}</Text>
    )

  const tokenString = user?.stream_token ? `?token=${user.stream_token}` : ""

  const serverAddress = VITE_API_URL
  const username = user?.username || "any"
  const password = user?.stream_token || "any"
  const playlistUrl = `${VITE_API_URL}/iptv${tokenString}`
  const playlistM3uUrl = `${VITE_API_URL}/iptv.m3u${tokenString}`
  const playlistM3u8Url = `${VITE_API_URL}/iptv.m3u8${tokenString}`
  const epgXmlUrl = `${VITE_API_URL}/epg.xml${tokenString}`

  const xtreamItems = [
    { name: "Server / Portal URL", value: serverAddress },
    { name: "Username", value: username },
    { name: "Password", value: password },
  ]

  const longestxtreamItemValue = Math.max(
    ...xtreamItems.map((item) => item.value.length),
  )

  const iptvItems = [
    { name: "Playlist URL", value: playlistUrl },
    { name: "Playlist URL (.m3u)", value: playlistM3uUrl },
    { name: "Playlist URL (.m3u8)", value: playlistM3u8Url },
    { name: "EPG URL", value: epgXmlUrl },
  ]

  const longestiptvItemValue = Math.max(
    ...iptvItems.map((item) => item.value.length),
  )

  console.log(
    "xtream len: ",
    longestxtreamItemValue,
    " iptv len: ",
    longestiptvItemValue,
  )

  return (
    <VStack gap={6} align="stretch">
      <VStack gap={2} align="stretch">
        <Heading>Xtream IPTV</Heading>
        <Text>
          Add a playlist/source with your IPTV app, use the XC/Xtream setting
          when adding. EPG should work automatically. If its not available,
          follow the regular IPTV instructions.
        </Text>
        <Box maxW={{ base: "100%", sm: "450px" }}>
          <AppTableRoot preset="outlineSm" width="100%" maxWidth="100%">
            <TableBody>{renderTableRows(xtreamItems)}</TableBody>
          </AppTableRoot>
        </Box>
      </VStack>

      <VStack gap={2} align="stretch">
        <Heading>IPTV</Heading>
        <Text>
          Depending on the app, you might need to use an alternate Playlist or
          EPG url.
        </Text>
        <Text>Some apps will only work if this site is on https.</Text>
        <Box maxW={{ base: "100%", md: "700px" }}>
          <AppTableRoot preset="outlineSm" width="100%" maxWidth="100%">
            <TableBody>{renderTableRows(iptvItems)}</TableBody>
          </AppTableRoot>
        </Box>
      </VStack>
    </VStack>
  )
}
