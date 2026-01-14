import { Box, Heading, Text, VStack } from "@chakra-ui/react"
import { Code } from "@/components/ui/code"
import { RouterLink } from "@/components/ui/routerlink"

export function PlaybackInfo() {
  return (
    <VStack gap={6} align="stretch">
      <Box>
        <Heading>What is this?</Heading>
        <Text>
          A webapp that rehosts Ace Streams, allowing watching by a webplayer,
          media player, or IPTV player.
        </Text>
        <Text>
          This page details manual playback of a stream, for the best experience
          i'd recommend using and iptv app and following the guide at on the{" "}
          <RouterLink to="/info/iptv">IPTV Info Page</RouterLink>.
        </Text>
        <Text>
          If you are experiencing constant buffering, pause the stream for two minutes.
        </Text>
      </Box>

      <Box>
        <Heading>Web Player Limitations</Heading>
        <Text>
          If the stream has a codec that browsers don't support (AC3, DTS),
          audio will not work.
        </Text>
        <Text>
          If the source drops, or changes video stream, the video player will
          freeze, click the reload player button.
        </Text>
        <Text>
          To avoid web player limitations, use an external player / IPTV player.
        </Text>
      </Box>

      <Box>
        <VStack gap={4} align="stretch">
          <Box>
            <Heading>Playing with an External Media Player</Heading>
            <Text>
              To play a stream with an external player, copy the Direct (stream)
              URL.
            </Text>
          </Box>

          <Box>
            <Heading size="sm">VLC (Linux, MacOS, Windows)</Heading>
            <Text>
              On Computer, go to Media &gt; Open Network Stream, paste the
              Direct URL and click Open.
            </Text>
            <Text>
              On Mobile, go to Browse, Open Network Stream, Paste the Direct URL
              and click Open Network Stream
            </Text>
          </Box>
          <Box>
            <Heading size="sm">IINA (MacOS)</Heading>
            <Text>
              Open IINA and select "Open URL" from the menu. Paste the Direct
              URL and click Open.
            </Text>
          </Box>
          <Box>
            <Heading size="sm">MPV (Linux, MacOS, Windows)</Heading>
            <Text>
              Run <Code>mpv &lt;Direct URL&gt;</Code> in a terminal.
            </Text>
            <Text>
              If you would like safer buffering, add the command line arguments:
            </Text>
            <Code>
              --cache=auto --cache-secs=240 --cache-pause=yes
              --cache-pause-wait=5 --cache-pause-initial=yes
            </Code>
            <Text>
              You can add these to mpv.conf as well. Pause and let it cache
              extra if you want.
            </Text>
            <Text>
              On MacOS you will first need to make a symlink to your path:
            </Text>
            <Code>
              sudo ln -s /Applications/mpv.app/Contents/MacOS/mpv
              /usr/local/bin/mpv
            </Code>
          </Box>
        </VStack>
      </Box>
    </VStack>
  )
}
