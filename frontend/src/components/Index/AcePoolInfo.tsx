import { Box, Heading, HStack, Link, Text } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { FiAlertTriangle, FiSearch } from "react-icons/fi"
import { AcePoolService, StreamsService } from "@/client"
import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import baseURL from "@/helpers"
import { loadPlayStream } from "@/hooks/useVideoPlayer"
import { STATUS_COLORS } from "./constants"
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
      <TableCell
        maxW="250px"
        overflow="hidden"
        textOverflow="ellipsis"
        whiteSpace="nowrap"
        textAlign={"center"}
      >
        <Link onClick={() => loadPlayStream(data?.content_id)}>
          {data?.title || "N/A"}
        </Link>
      </TableCell>
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
    error,
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
    return (
      <HStack>
        <FiSearch />
        Fetching acestream information...
      </HStack>
    )
  }

  if (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)

    return (
      <Box>
        <Text color={STATUS_COLORS.error}>
          Backend is unavailable: {errorMessage}
        </Text>
      </Box>
    )
  }

  if (!acePoolData) {
    return (
      <Text color={STATUS_COLORS.error}>Unable to fetch Ace Pool info</Text>
    )
  }

  return (
    // For when there is an api mismatch
    <Box>
      <Heading size="sm">AceStream Backend Information</Heading>
      {acePoolData && acePoolData.external_url !== VITE_API_URL && (
        <Box p={2} border={"1px solid orange"} my={2}>
          <HStack>
            <Text color={STATUS_COLORS.warning} fontSize="xl">
              <FiAlertTriangle />
            </Text>
            <Box>
              <Text color={STATUS_COLORS.warning} fontWeight="bold">
                Backend URL ({acePoolData.external_url}) != Frontend API URL (
                {VITE_API_URL}).
              </Text>
              <Text color={STATUS_COLORS.warning} fontWeight="bold">
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
              <Text>
                If the frontend url in this is something weird, the frontend was
                built with that specific VITE_API_URL specified.
              </Text>
            </Box>
          </HStack>
        </Box>
      )}
      <AppTableRoot preset="outlineSm" maxW="400px">
        <TableHeader>
          <TableRow>
            <TableColumnHeader>Version</TableColumnHeader>
            <TableColumnHeader>Streams</TableColumnHeader>
            <TableColumnHeader>Transcode Audio</TableColumnHeader>
            <TableColumnHeader>Health</TableColumnHeader>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow opacity={isPlaceholderData ? 0.5 : 1}>
            <TableCell
              textAlign={"center"}
              color={
                !acePoolData.ace_version ||
                acePoolData.ace_version === "unknown"
                  ? STATUS_COLORS.error
                  : undefined
              }
            >
              {acePoolData.ace_version || "N/A"}
            </TableCell>
            <TableCell textAlign={"center"}>
              {acePoolData.ace_instances.length}/{acePoolData.max_size ?? "N/A"}
            </TableCell>
            <TableCell textAlign={"center"}>
              {acePoolData.transcode_audio ? "Yes" : "No"}
            </TableCell>
            <TableCell
              textAlign={"center"}
              color={!acePoolData.healthy ? STATUS_COLORS.error : undefined}
            >
              {acePoolData.healthy ? "Healthy" : "Unhealthy"}
            </TableCell>
          </TableRow>
        </TableBody>
      </AppTableRoot>
      {acePoolData.ace_instances.length !== 0 && (
        <Box mt={4}>
          <Heading size="sm">AceStream Instances</Heading>
          <Box overflowX="auto" maxWidth="fit-content" p={1}>
            <AppTableRoot preset="outlineSm">
              <TableHeader>
                <TableRow>
                  <TableColumnHeader>#</TableColumnHeader>
                  <TableColumnHeader>Status</TableColumnHeader>
                  <TableColumnHeader>Quality</TableColumnHeader>
                  <TableColumnHeader>Currently Playing</TableColumnHeader>
                  <TableColumnHeader>Make Available</TableColumnHeader>
                </TableRow>
              </TableHeader>
              <TableBody>
                {acePoolData.ace_instances.map((instance, index) => (
                  <TableRow key={index}>
                    <TableCell textAlign={"center"}>
                      {instance.ace_pid}
                    </TableCell>
                    <TableCell textAlign={"center"}>
                      {instance.locked_in
                        ? `🔒 Locked for (${Math.floor((instance.time_until_unlock ?? 0) / 60)}:${((instance.time_until_unlock ?? 0) % 60).toString().padStart(2, "0")})`
                        : "Available"}
                    </TableCell>
                    <InstanceQuality contentId={instance.content_id} />
                    <TableCell textAlign={"center"}>
                      {instance.locked_in ? (
                        <Link
                          colorPalette="red"
                          onClick={() =>
                            deleteStreamMutation.mutate(instance.content_id)
                          }
                          cursor="pointer"
                        >
                          🔓 Unlock Instance
                        </Link>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </AppTableRoot>
          </Box>
        </Box>
      )}
    </Box>
  )
}
