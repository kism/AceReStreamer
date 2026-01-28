import { Box, Heading, Link } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { AcePoolForApi } from "@/client"
import { AcePoolService, StreamsService } from "@/client"
import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { QualityCell } from "./QualityCell"

const loadVideoPlayerModule = () => import("@/hooks/useVideoPlayer")

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
        <Link
          onClick={() =>
            loadVideoPlayerModule().then((module) => {
              module.loadPlayStream(data?.content_id)
            })
          }
        >
          {data?.title || "N/A"}
        </Link>
      </TableCell>
    </>
  )
}

interface AcePoolInstancesTableProps {
  acePoolData: AcePoolForApi
}

export function AcePoolInstancesTable({
  acePoolData,
}: AcePoolInstancesTableProps) {
  const queryClient = useQueryClient()

  const deleteStreamMutation = useMutation({
    mutationFn: (contentId: string) =>
      AcePoolService.deleteByContentId({ contentId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ace_instances"] })
    },
  })

  if (acePoolData.ace_instances.length === 0) {
    return null
  }

  return (
    <Box>
      <Heading size="sm" py={1}>
        AceStream Instances
      </Heading>
      <AppTableRoot preset="outlineSm" maxW="fit-content">
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
          {acePoolData.ace_instances.map((instance, index: number) => (
            <TableRow key={index}>
              <TableCell textAlign={"center"}>{instance.ace_pid}</TableCell>
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
  )
}
