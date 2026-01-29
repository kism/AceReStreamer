import { Box, Flex, Heading, HStack, Text, VStack } from "@chakra-ui/react"
import { Link } from "@/components/ui/link"

export function AppsInfo() {
  const apps = [
    {
      platform: ["iOS", "Apple TV", "Android", "Android TV"],
      name: "iMPlayer",
      m3u8: "✅",
      xc: "✅",
      epg: "✅",
      links: [{ url: "https://implayer.tv/home", label: "Website" }],
      notes:
        "Great free multiplatform player. More than two playlists, auto epg refresh require a subscription.",
    },
    {
      platform: ["iOS, Apple TV"],
      name: "UHF",
      m3u8: "✅",
      xc: "✅",
      epg: "✅",
      links: [
        {
          url: "https://apps.apple.com/us/app/uhf-love-your-iptv/id6443751726",
          label: "App Store",
        },
      ],
      notes:
        "Best app I have used, has ads and a watermark if you don't pay. $60 AUD for a lifetime license.",
    },
    {
      platform: ["iOS, Apple TV"],
      name: "Flex IPTV",
      m3u8: "✅",
      xc: "❌",
      epg: "❌",
      links: [
        {
          url: "https://apps.apple.com/us/app/flex-iptv/id1182930255",
          label: "App Store",
        },
      ],
      notes:
        "Best free iOS player, need to unlock screen rotation to get video landscape.",
    },
    {
      platform: ["Android TV"],
      name: "TiviMate",
      m3u8: "✅",
      xc: "✅",
      epg: "✅",
      links: [
        {
          url: "https://play.google.com/store/apps/details?id=ar.tvplayer.tv",
          label: "Google Play",
        },
      ],
      notes:
        "Great player for Android TV, most features require a one time $50 AUD payment.",
    },
    {
      platform: ["Android TV"],
      name: "Sparkle TV",
      m3u8: "✅",
      xc: "✅",
      epg: "✅",
      links: [
        {
          url: "https://play.google.com/store/apps/details?id=se.hedekonsult.sparkle",
          label: "Google Play",
        },
      ],
      notes: "Good player for Android TV",
    },
    {
      platform: ["Roku", "LG", "Samsung"],
      name: "IPTV Pro by X-PLAYERS",
      m3u8: "✅",
      xc: "❔",
      epg: "❔",
      links: [{ url: "https://iptvproplayer.live/", label: "Website" }],
      notes:
        "7 day trial, one-off paid IPTV app for Smart TVs, haven't tested EPG",
    },
    {
      platform: ["Android", "Android TV"],
      name: "M3UAndroid",
      m3u8: "✅",
      xc: "✅",
      epg: "❔",
      links: [
        {
          url: "https://github.com/oxyroid/M3UAndroid",
          label: "GitHub",
        },
        {
          url: "https://apt.izzysoft.de/fdroid/index/apk/com.m3u.androidApp",
          label: "IzzyOnDroid",
        },
      ],
      notes:
        "Not on play store, you have to install manually, not sure how the epg works on mobile.",
    },
    {
      platform: ["Android TV"],
      name: "TV IRL",
      m3u8: "✅",
      xc: "❌",
      epg: "❔",
      links: [
        {
          url: "https://play.google.com/store/apps/details?id=by.stari4ek.tvirl",
          label: "Google Play",
        },
      ],
      notes: [
        "Only use on Sony, TCL or other integrated Android TV devices.",
        "Integrates with the regular TV listings.",
        "User interface is weird.",
      ],
    },
  ]

  return (
    <VStack gap={2} align="stretch">
      <VStack gap={1} align="stretch">
        <Heading>Recommended Apps</Heading>
        <Text>
          Many apps are made to be players for their subscription IPTV services,
          and on the side offer loading external playlists.
        </Text>
      </VStack>

      <VStack gap={1} align="stretch">
        <Heading size={"sm"}>Tested to work</Heading>

        <Flex gap={2} align="stretch" wrap="wrap">
          {apps.map((app) => (
            <Box
              key={app.name}
              borderWidth="1px"
              p={4}
              width={{ base: "100%", sm: "400px" }}
            >
              <VStack align="stretch" gap={2}>
                <Text>
                  <strong>{app.name}</strong> on {app.platform.join(", ")}
                </Text>

                <HStack gap={4}>
                  <Text>{app.m3u8} m3u8</Text>
                  <Text>{app.xc} XC</Text>
                  <Text>{app.epg} EPG</Text>
                </HStack>

                <Text>
                  {app.links.map((link, i) => (
                    <span key={link.url}>
                      <Link
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {link.label}
                      </Link>
                      {i < app.links.length - 1 && ", "}
                    </span>
                  ))}
                </Text>
                <Text>
                  {Array.isArray(app.notes)
                    ? app.notes.map((note, i) => (
                        <span key={i}>
                          {note}
                          {i < app.notes.length - 1 && <br />}
                        </span>
                      ))
                    : app.notes}
                </Text>
              </VStack>
            </Box>
          ))}
        </Flex>
      </VStack>

      <Box>
        <Heading size={"sm"}>Tested to work, but not recommended</Heading>
        <Text>ProgTV, Weird skipping/looping issue</Text>
        <Text>IPTV Smarters, Ads unless you pay, interface not great</Text>
        <Text>
          Purple Simple, must set HLS and use internal software player, no
          acceleration
        </Text>
      </Box>
      <Box>
        <Heading size={"sm"}>Tested, not working</Heading>
        <Text>Jellyfin app, will try fix</Text>
        <Text>UniTV</Text>
        <Text>DangoPlayer</Text>
        <Text>Opus</Text>
        <Text>1-Stream Player by Purple</Text>
      </Box>
    </VStack>
  )
}

export function OtherIptvSources() {
  return (
    <Box>
      <Heading>More IPTV Sources</Heading>
      <Text>
        <Link
          href="https://bugsfreeweb.github.io/LiveTVCollector/"
          target="_blank"
          rel="noopener noreferrer"
        >
          Live TV Collector
        </Link>
      </Text>
      <Text>
        <Link
          href="https://iptv-org.github.io/iptv/"
          target="_blank"
          rel="noopener noreferrer"
        >
          iptv-org collection
        </Link>
      </Text>
    </Box>
  )
}
