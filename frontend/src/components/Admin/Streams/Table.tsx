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
import { StreamsService } from "@/client"
import { getQualityColor } from "@/components/Index/QualityCell"
import { Button } from "@/components/ui/button"

function getStreamsQueryOptions() {
  return {
    queryFn: () => StreamsService.streams(),
    queryKey: ["items"],
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

function StreamAdminTable() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    ...getStreamsQueryOptions(),
    placeholderData: (prevData) => prevData,
  })

  const mutation = useMutation({
    mutationFn: (contentId: string) =>
      StreamsService.deleteByContentId({ contentId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] })
    },
  })

  const handleRemoveByContentId = useCallback(
    (slug: string) => {
      if (mutation.isPending) {
        return // Prevent multiple calls while one is in progress
      }
      console.log("Deleting stream with content ID:", slug)
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
        Streams Management
      </Heading>
      <VStack align="start">
        {items?.map((item) => (
          <Box
            key={item.content_id}
            px={2}
            py={1}
            borderWidth="1px"
            width="full"
          >
            <Flex width="full" flexDirection="column" gap={1}>
              <Flex justify="space-between" align="center" width="full">
                <Heading size="sm" py={0}>
                  {item.title}
                </Heading>
                <Button
                  size="2xs"
                  colorPalette="red"
                  onClick={() => handleRemoveByContentId(item.content_id)}
                >
                  Delete
                </Button>
              </Flex>
              <Flex flexWrap="wrap" gap={1} fontSize={"xs"} alignItems="center">
                <Box flex="0 1 auto" bg="bg.muted" px={2} py={1}>
                  Content ID:{" "}
                  <Code backgroundColor="bg.emphasized">{item.content_id}</Code>
                </Box>
                <Box flex="0 1 auto" bg="bg.muted" px={2} py={1}>
                  Infohash:{" "}
                  <Code backgroundColor="bg.emphasized">
                    {item.infohash ?? "???"}
                  </Code>
                </Box>
              </Flex>
              <Flex flexWrap="wrap" gap={1} fontSize={"xs"} alignItems="center">
                <HStack flex="0 1 auto" bg="bg.muted" px={2} py={1}>
                  Last scrape time:
                  {GetRelativeTimeText(item.last_scraped_time)}
                </HStack>
                <HStack flex="0 1 auto" bg="bg.muted" px={2} py={1}>
                  <Text>Has ever worked: </Text>
                  <Text
                    color={item.has_ever_worked ? "fg.success" : "fg.error"}
                  >
                    {item.has_ever_worked ? "Yes" : "No"}
                  </Text>
                  {item.m3u_failures > 0 && (
                    <Text>(Failures to load: {item.m3u_failures})</Text>
                  )}
                  {item.m3u_failures === 0 && !item.has_ever_worked && (
                    <Text>(Never loaded)</Text>
                  )}
                </HStack>
                <HStack flex="0 1 auto" bg="bg.muted" px={2} py={1}>
                  Quality:
                  <Text color={getQualityColor(Number(item.quality))}>
                    {item.quality !== -1 ? item.quality : "???"}
                  </Text>
                </HStack>
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

export default StreamAdminTable
