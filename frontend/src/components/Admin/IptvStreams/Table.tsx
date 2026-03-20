import {
  Box,
  Code,
  Flex,
  Heading,
  HStack,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback } from "react"
import { IptvStreamsService } from "@/client"
import { Button } from "@/components/ui/button"

function getIptvStreamsQueryOptions() {
  return {
    queryFn: () => IptvStreamsService.streams(),
    queryKey: ["iptvStreams"],
  }
}

function GetRelativeTimeText(timestamp: string) {
  const time = new Date(timestamp)
  const now = new Date()
  const diffInMs = now.getTime() - time.getTime()
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60))

  if (diffInMinutes < 1) {
    return <Text color="fg.success">just now</Text>
  }
  if (diffInMinutes < 60) {
    return <Text color="fg.success">{`${diffInMinutes} minute(s) ago`}</Text>
  }
  if (diffInMinutes < 1440) {
    const hours = Math.floor(diffInMinutes / 60)
    return <Text color="fg.success">{`${hours} hour(s) ago`}</Text>
  }
  const days = Math.floor(diffInMinutes / 1440)
  return (
    <Text
      color={days > 1 ? "fg.error" : "fg.success"}
    >{`${days} day(s) ago`}</Text>
  )
}

function IptvStreamAdminTable() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    ...getIptvStreamsQueryOptions(),
    placeholderData: (prevData) => prevData,
  })

  const mutation = useMutation({
    mutationFn: (slug: string) => IptvStreamsService.deleteBySlug({ slug }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["iptvStreams"] })
    },
  })

  const handleRemoveBySlug = useCallback(
    (slug: string) => {
      if (mutation.isPending) {
        return
      }
      mutation.mutate(slug)
    },
    [mutation],
  )

  if (isLoading) {
    return <Box>Loading...</Box>
  }

  const items = data ?? []

  return (
    <>
      <Heading size="md" mt={2} mb={1}>
        IPTV Streams Management
      </Heading>
      <VStack align="start">
        {items?.map((item) => (
          <Box key={item.slug} px={2} py={1} borderWidth="1px" width="full">
            <Flex width="full" flexDirection="column" gap={1}>
              <Flex justify="space-between" align="center" width="full">
                <Heading size="sm" py={0}>
                  {item.title}
                </Heading>
                <Button
                  size="2xs"
                  colorPalette="red"
                  onClick={() => handleRemoveBySlug(item.slug)}
                >
                  Delete
                </Button>
              </Flex>
              <Flex flexWrap="wrap" gap={1} fontSize={"xs"} alignItems="center">
                <Box flex="0 1 auto" bg="bg.muted" px={2} py={1}>
                  Slug: <Code backgroundColor="bg.emphasized">{item.slug}</Code>
                </Box>
                <Box flex="0 1 auto" bg="bg.muted" px={2} py={1}>
                  Source:{" "}
                  <Code backgroundColor="bg.emphasized">
                    {item.source_name}
                  </Code>
                </Box>
              </Flex>
              <Flex flexWrap="wrap" gap={1} fontSize={"xs"} alignItems="center">
                <HStack flex="0 1 auto" bg="bg.muted" px={2} py={1}>
                  Last scrape time:
                  {GetRelativeTimeText(item.last_scraped_time)}
                </HStack>
                <Box flex="0 1 auto" bg="bg.muted" px={2} py={1}>
                  Group:{" "}
                  <Code backgroundColor="bg.emphasized">
                    {item.group_title}
                  </Code>
                </Box>
              </Flex>
              <Flex flexWrap="wrap" gap={1} fontSize={"xs"} alignItems="center">
                <Box flex="0 1 auto" bg="bg.muted" px={2} py={1}>
                  TVG ID:{" "}
                  <Code backgroundColor="bg.emphasized">{item.tvg_id}</Code>
                </Box>
                <Box flex="0 1 auto" bg="bg.muted" px={2} py={1}>
                  TVG Logo:{" "}
                  <Code backgroundColor="bg.emphasized">{item.tvg_logo}</Code>
                </Box>
                <HStack flex="0 1 auto" bg="bg.muted" px={2} py={1}>
                  Program:
                  <Text
                    maxW="200px"
                    overflow="hidden"
                    textOverflow="ellipsis"
                    whiteSpace="nowrap"
                    color={item.program_title !== "" ? "fg" : "fg.error"}
                  >
                    {item.program_title !== "" ? item.program_title : "???"}
                  </Text>
                </HStack>
              </Flex>
            </Flex>
          </Box>
        ))}
      </VStack>
    </>
  )
}

export default IptvStreamAdminTable
