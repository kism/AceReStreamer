import {
  Box,
  Code,
  Editable,
  Flex,
  Heading,
  HStack,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useState } from "react"
import { FaPencilAlt } from "react-icons/fa"
import { FiPlay } from "react-icons/fi"
import {
  type FoundAceStreamAPI,
  ScraperService,
  StreamsService,
} from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { PreviewDialog } from "@/components/Admin/Streams/PreviewDialog"
import { getQualityColor } from "@/components/Index/QualityCell"
import { Button } from "@/components/ui/button"
import { CopyButton } from "@/components/ui/copy-button"
import { Loading } from "@/components/ui/loading"
import baseURL from "@/helpers"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

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
  const { showSuccessToast } = useCustomToast()
  const [previewStream, setPreviewStream] = useState<FoundAceStreamAPI | null>(
    null,
  )

  const { data, isLoading } = useQuery({
    queryFn: () => StreamsService.streams(),
    queryKey: ["items"],
    placeholderData: (prevData) => prevData,
  })

  const mutation = useMutation({
    mutationFn: (contentId: string) =>
      StreamsService.deleteByContentId({ contentId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] })
    },
  })

  const renameMutation = useMutation({
    // Override both keys so the rename sticks whichever one a scraper finds
    mutationFn: async (data: {
      contentId: string
      infohash: string | null | undefined
      name: string
    }) => {
      await ScraperService.addNameOverride({
        contentId: data.contentId,
        name: data.name,
      })
      if (data.infohash) {
        await ScraperService.addNameOverride({
          contentId: data.infohash,
          name: data.name,
        })
      }
    },
    onSuccess: () => {
      showSuccessToast("Name override added successfully.")
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] })
    },
  })

  const handleRename = useCallback(
    (item: FoundAceStreamAPI, name: string) => {
      const trimmed = name.trim()
      if (!trimmed || trimmed === item.title || renameMutation.isPending) {
        return
      }
      renameMutation.mutate({
        contentId: item.content_id,
        infohash: item.infohash,
        name: trimmed,
      })
    },
    [renameMutation],
  )

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
    return <Loading />
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
                <Editable.Root
                  key={item.title}
                  defaultValue={item.title}
                  onValueCommit={(e) => handleRename(item, e.value)}
                  activationMode="dblclick"
                  size="sm"
                  fontWeight="bold"
                  flex="1"
                  mr={2}
                >
                  <Editable.Preview />
                  <Editable.Input />
                  <Editable.Control>
                    <Editable.EditTrigger asChild>
                      <Button size="2xs" variant="ghost" color="ui.main">
                        <FaPencilAlt />
                      </Button>
                    </Editable.EditTrigger>
                  </Editable.Control>
                </Editable.Root>
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
                  <Code backgroundColor="bg.emphasized">
                    {item.tvg_id || "-"}
                  </Code>
                </Box>
                <Box flex="0 1 auto" bg="bg.muted" px={2} py={1}>
                  TVG Logo:{" "}
                  <Code backgroundColor="bg.emphasized">
                    {item.tvg_logo || "-"}
                  </Code>
                </Box>
              </Flex>
              <HStack bg="bg.muted" px={2} py={1} minWidth={0}>
                <Text flexShrink={0}>Stream URL:</Text>
                <Code
                  backgroundColor="bg.emphasized"
                  overflowX="auto"
                  whiteSpace="nowrap"
                  display="block"
                  flex={1}
                  minWidth={0}
                >
                  {`${baseURL()}/hls/${item.content_id}`}
                </Code>
                <CopyButton text={`${baseURL()}/hls/${item.content_id}`} />
                <Button
                  size="2xs"
                  p="0"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  onClick={() => setPreviewStream(item)}
                >
                  <FiPlay />
                </Button>
              </HStack>
            </Flex>
          </Box>
        ))}
      </VStack>
      <PreviewDialog
        stream={previewStream}
        onClose={() => setPreviewStream(null)}
      />
    </>
  )
}

export default StreamAdminTable
