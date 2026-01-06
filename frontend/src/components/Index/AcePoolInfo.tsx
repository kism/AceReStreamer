import { Box, HStack, Link, Table, Text } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { FiAlertTriangle, FiSearch } from "react-icons/fi"
import { AcePoolService, StreamsService } from "@/client"
import baseURL from "@/helpers"
import { loadPlayStream } from "@/hooks/useVideoPlayer"
import { QualityCell } from "./QualityCell"

const VITE_API_URL = baseURL()

function getStreamQueryOptions(content_id: string) {
  return {
    queryFn: () => StreamsService.byContentId({ contentId: content_id }),
    queryKey: ["content_id", content_id],
  }
}

function InstanceQuality({ contentId }: { contentId: string }) {
  const { data } = useQuery({
    ...getStreamQueryOptions(contentId),
    enabled: !!contentId,
    refetchInterval: 30000, // Refetch every 30 seconds
  })
  return (
    <>
      <QualityCell quality={data?.quality ?? -1} />
      <Table.Cell textAlign={"center"} p={2}>
        <Link onClick={() => loadPlayStream(data?.content_id)}>
          {data?.title || "N/A"}
        </Link>
      </Table.Cell>
    </>
  )
}

function getAcePoolQueryOptions() {
  return {
    queryFn: () => AcePoolService.pool(),
    queryKey: ["ace_instances"],
  }
}

export function AcePoolInfo() {
  const queryClient = useQueryClient()
  const {
    data: acePoolData,
    isLoading,
    isPlaceholderData,
  } = useQuery({
    ...getAcePoolQueryOptions(),
    placeholderData: (prevData) => prevData,
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const deleteStreamMutation = useMutation({
    mutationFn: (contentId: string) =>
      AcePoolService.deleteByContentId({ contentId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ace_instances"] })
    },
  })

  if (isLoading) {
    return <FiSearch />
  }

  if (!acePoolData) {
    return (
      <Text mt={4} color="red.500">
        Unable to fetch Ace Pool info
      </Text>
    )
  }

  return (
    <Box>
      <Text>AceStream Backend Information</Text>
      {acePoolData && acePoolData.external_url !== VITE_API_URL && (
        <Box p={2} border={"1px solid orange"} my={2}>
          <HStack>
            <Text color="orange.500" fontSize="xl">
              <FiAlertTriangle />
            </Text>
            <Box>
              <Text color="orange.500" fontWeight="bold">
                Backend URL ({acePoolData.external_url}) != Frontend API URL (
                {VITE_API_URL}).
              </Text>
              <Text color="orange.500" fontWeight="bold">
                VIDEO STREAMING WILL NOT WORK
              </Text>
              <Text>
                In FastAPI, ensure that EXTERNAL_URL config option is set
                correctly.
              </Text>
              <Text>
                If you are hosting the frontend separately, ensure that
                VITE_API_URL is set correctly.
              </Text>
            </Box>
          </HStack>
        </Box>
      )}
      <Table.Root size="sm" variant="outline" maxW="400px" mt={2}>
        <Table.Header>
          <Table.Row>
            <Table.Cell textAlign={"center"} p={2}>
              Version
            </Table.Cell>
            <Table.Cell textAlign={"center"} p={2}>
              Streams
            </Table.Cell>
            <Table.Cell textAlign={"center"} p={2}>
              Transcode Audio
            </Table.Cell>
            <Table.Cell textAlign={"center"} p={2}>
              Health
            </Table.Cell>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          <Table.Row opacity={isPlaceholderData ? 0.5 : 1}>
            <Table.Cell
              textAlign={"center"}
              p={2}
              color={!acePoolData.ace_version || acePoolData.ace_version === "unknown" ? "red.500" : undefined}
            >
              {acePoolData.ace_version || "N/A"}
            </Table.Cell>
            <Table.Cell textAlign={"center"} p={2}>
              {acePoolData.ace_instances.length}/{acePoolData.max_size ?? "N/A"}
            </Table.Cell>
            <Table.Cell textAlign={"center"} p={2}>
              {acePoolData.transcode_audio ? "Yes" : "No"}
            </Table.Cell>
            <Table.Cell
              textAlign={"center"}
              p={2}
              color={!acePoolData.healthy ? "red.500" : undefined}
            >
              {acePoolData.healthy ? "Healthy" : "Unhealthy"}
            </Table.Cell>
          </Table.Row>
        </Table.Body>
      </Table.Root>
      {acePoolData.ace_instances.length !== 0 && (
        <Box mt={4}>
          <Text>Currently loaded streams</Text>
          <Table.Root size="sm" variant="outline" mt={2}>
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader textAlign={"center"} p={2}>
                  #
                </Table.ColumnHeader>
                <Table.ColumnHeader textAlign={"center"} p={2}>
                  Status
                </Table.ColumnHeader>
                <Table.ColumnHeader textAlign={"center"} p={2}>
                  Quality
                </Table.ColumnHeader>
                <Table.ColumnHeader textAlign={"center"} p={2}>
                  Currently Playing
                </Table.ColumnHeader>
                <Table.ColumnHeader textAlign={"center"} p={2}>
                  Make Available
                </Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {acePoolData.ace_instances.map((instance, index) => (
                <Table.Row key={index}>
                  <Table.Cell textAlign={"center"} p={2}>
                    {instance.ace_pid}
                  </Table.Cell>
                  <Table.Cell textAlign={"center"} p={2}>
                    {instance.locked_in
                      ? `🔒 Locked for (${Math.floor((instance.time_until_unlock ?? 0) / 60)}:${((instance.time_until_unlock ?? 0) % 60).toString().padStart(2, "0")})`
                      : "Available"}
                  </Table.Cell>
                  <InstanceQuality contentId={instance.content_id} />
                  <Table.Cell textAlign={"center"} p={2}>
                    <Link
                      colorPalette="red"
                      onClick={() =>
                        deleteStreamMutation.mutate(instance.content_id)
                      }
                      cursor="pointer"
                    >
                      Free
                    </Link>
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>
        </Box>
      )}
    </Box>
  )
}
