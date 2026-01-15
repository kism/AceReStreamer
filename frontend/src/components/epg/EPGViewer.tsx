import { Box, EmptyState, VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { FiCalendar } from "react-icons/fi"
import type { UserPublic } from "@/client"
import { MediaXmlService } from "@/client"
import { ChannelSelector } from "./ChannelSelector"
import { EPGTable } from "./EPGTable"
import { parseEPGXML } from "./utils"

interface EPGViewerProps {
  user: UserPublic | null
}

export function EPGViewer({ user }: EPGViewerProps) {
  const [selectedChannel, setSelectedChannel] = useState<string>("")

  const { data, isLoading, error } = useQuery({
    queryKey: ["epgXml", user?.stream_token],
    queryFn: async () => {
      try {
        console.log("Fetching EPG XML...")
        const response = await MediaXmlService.epgXml1({
          token: user?.stream_token,
        })
        console.log("EPG XML response type:", typeof response)
        console.log("EPG XML response length:", response?.toString().length)
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

  // Set default channel when data loads
  useEffect(() => {
    if (channels.length > 0 && !selectedChannel) {
      setSelectedChannel(channels[0].id)
    }
  }, [channels, selectedChannel])

  // Filter programmes by selected channel
  const programmes = selectedChannel
    ? allProgrammes.filter((prog) => prog.channel === selectedChannel)
    : []

  if (error) {
    return (
      <Box borderWidth="1px" overflow="hidden" p={4}>
        <EmptyState.Root>
          <EmptyState.Content>
            <EmptyState.Indicator>
              <FiCalendar />
            </EmptyState.Indicator>
            <VStack textAlign="center">
              <EmptyState.Title>Error loading EPG</EmptyState.Title>
              <EmptyState.Description>
                {error instanceof Error
                  ? error.message
                  : "Failed to load EPG data"}
              </EmptyState.Description>
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
      </Box>
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
      <Box borderWidth="1px" overflow="hidden">
        <EmptyState.Root>
          <EmptyState.Content>
            <EmptyState.Indicator>
              <FiCalendar />
            </EmptyState.Indicator>
            <VStack textAlign="center">
              <EmptyState.Title>No EPG data found</EmptyState.Title>
              <EmptyState.Description>
                Configure EPG sources in your settings.
              </EmptyState.Description>
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
      </Box>
    )
  }

  return (
    <VStack align="stretch" gap={4}>
      <ChannelSelector
        channels={channels}
        selectedChannel={selectedChannel}
        onChannelChange={setSelectedChannel}
      />
      <EPGTable programmes={programmes} />
    </VStack>
  )
}
