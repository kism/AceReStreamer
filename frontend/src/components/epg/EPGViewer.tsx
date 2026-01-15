import { Box, HStack, Text, VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import type { UserPublic } from "@/client"
import { MediaXmlService } from "@/client"
import { Checkbox } from "../ui/checkbox"
import { ChannelSelector } from "./ChannelSelector"
import { EPGTable } from "./EPGTable"
import { parseEPGXML, parseXmltvDate } from "./utils"

interface EPGViewerProps {
  user: UserPublic | null
}

export function EPGViewer({ user }: EPGViewerProps) {
  const [selectedChannel, setSelectedChannel] = useState<string>("")
  const [hidePastPrograms, setHidePastPrograms] = useState<boolean>(true)

  const { data, isLoading, error } = useQuery({
    queryKey: ["epgXml", user?.stream_token],
    queryFn: async () => {
      try {
        const response = await MediaXmlService.epgXml1({
          token: user?.stream_token,
        })
        return parseEPGXML(response as string)
      } catch (err) {
        console.error("Error fetching EPG:", err)
        throw err
      }
    },
    retry: false,
    enabled: !!user?.stream_token,
  })

  const channels = data?.channels || []
  const allProgrammes = data?.programmes || []

  useEffect(() => {
    // Set default channel
    if (channels.length > 0 && !selectedChannel) {
      setSelectedChannel(channels[0].id)
    }
  }, [channels, selectedChannel])

  // Filter programmes by selected channel and optionally hide past programs
  const now = new Date()
  const programmes = selectedChannel
    ? allProgrammes.filter((prog) => {
        if (prog.channel !== selectedChannel) return false
        if (hidePastPrograms && parseXmltvDate(prog.stop) < now) return false
        return true
      })
    : []

  if (error) {
    return (
      <VStack align="stretch" gap={4}>
        <Text>Error loading EPG</Text>
        <Text>{(error as Error).message}</Text>
      </VStack>
    )
  }

  if (isLoading) {
    return (
      <VStack align="stretch" gap={4}>
        <Box>Loading EPG data...</Box>
      </VStack>
    )
  }

  if (channels.length === 0) {
    return (
      <VStack align="stretch" gap={4}>
        <Text>No EPG data found. Configure EPG sources in your settings.</Text>
      </VStack>
    )
  }

  return (
    <VStack align="stretch" gap={4}>
      <HStack>
        <ChannelSelector
          channels={channels}
          selectedChannel={selectedChannel}
          onChannelChange={setSelectedChannel}
        />
        <Checkbox
          checked={hidePastPrograms}
          onCheckedChange={({ checked }) => setHidePastPrograms(!!checked)}
        >
          Hide past programs
        </Checkbox>
      </HStack>
      <EPGTable programmes={programmes} />
    </VStack>
  )
}
