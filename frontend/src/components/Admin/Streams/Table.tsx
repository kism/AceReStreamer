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
      <Heading>Streams Management</Heading>
      <VStack align="start">
        {items?.map((item) => (
          <Box
            key={item.content_id}
            p={4}
            borderWidth="1px"
            borderRadius="md"
            width="full"
          >
            <Flex justify="space-between" width="full">
              <VStack align="start" gap={1} p={0}>
                <Heading size="md">{item.title}</Heading>
                <HStack>
                  Last scrape time:
                  {GetRelativeTimeText(item.last_scraped_time)}
                </HStack>
                <HStack>
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
                <HStack>
                  Quality:
                  <Text color={getQualityColor(Number(item.quality))}>
                    {item.quality !== -1 ? item.quality : "???"}
                  </Text>
                </HStack>
                <Box>
                  TVG ID: <Code>{item.tvg_id}</Code>
                </Box>
                <Box>
                  TVG Logo: <Code>{item.tvg_logo}</Code>
                </Box>
                <HStack>
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
              </VStack>
              <VStack align="start" gap={2} p={0}>
                <Box border={"1px solid"} borderColor="fg.subtle" p={1}>
                  <Text m={0} p={0}>
                    Content ID
                  </Text>
                  <Code p={0}>{item.content_id}</Code>
                </Box>
                <Box border={"1px solid"} borderColor="fg.subtle" p={1}>
                  <Text m={0} p={0}>
                    Infohash
                  </Text>
                  <Code p={0}>{item.infohash ?? "???"}</Code>
                </Box>
                <Button
                  size="xs"
                  backgroundColor="fg.error"
                  onClick={() => handleRemoveByContentId(item.content_id)}
                >
                  Delete
                </Button>
              </VStack>
            </Flex>
          </Box>
        ))}
      </VStack>
    </>
  )
}

export default StreamAdminTable
