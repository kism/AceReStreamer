import { Box, Heading, Link } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { AcePoolForApi, IPTVPoolForAPI } from "@/client"
import {
  AcePoolService,
  AceStreamsService,
  IptvPoolService,
  IptvStreamsService,
} from "@/client"
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

function AceInstanceQuality({ contentId }: { contentId: string }) {
  const { data } = useQuery({
    queryFn: () => AceStreamsService.byContentId({ contentId }),
    queryKey: ["content_id", contentId],
    enabled: !!contentId,
    refetchInterval: 30000,
  })
  return <QualityCell quality={data?.quality ?? -1} />
}

function AceInstanceTitle({ contentId }: { contentId: string }) {
  const { data } = useQuery({
    queryFn: () => AceStreamsService.byContentId({ contentId }),
    queryKey: ["content_id", contentId],
    enabled: !!contentId,
    refetchInterval: 30000,
  })
  return (
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
            module.loadPlayStream(`/hls/ace/${data?.content_id}`)
          })
        }
      >
        {data?.title || "N/A"}
      </Link>
    </TableCell>
  )
}

function IptvInstanceQuality({ slug }: { slug: string }) {
  const { data } = useQuery({
    queryFn: () => IptvStreamsService.bySlug({ slug }),
    queryKey: ["iptv_slug", slug],
    enabled: !!slug,
    refetchInterval: 30000,
  })
  return <QualityCell quality={data?.quality ?? -1} />
}

function IptvInstanceTitle({ slug }: { slug: string }) {
  const { data } = useQuery({
    queryFn: () => IptvStreamsService.bySlug({ slug }),
    queryKey: ["iptv_slug", slug],
    enabled: !!slug,
    refetchInterval: 30000,
  })
  return (
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
            module.loadPlayStream(`/hls/web/${slug}`)
          })
        }
      >
        {data?.title || slug}
      </Link>
    </TableCell>
  )
}

function formatTime(seconds: number) {
  return `${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, "0")}`
}

interface PoolInstancesTableProps {
  acePoolData: AcePoolForApi
  iptvPoolData: IPTVPoolForAPI | undefined
}

export function PoolInstancesTable({
  acePoolData,
  iptvPoolData,
}: PoolInstancesTableProps) {
  const queryClient = useQueryClient()

  const deleteAceMutation = useMutation({
    mutationFn: (contentId: string) =>
      AcePoolService.deleteByContentId({ contentId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ace_instances"] })
    },
  })

  const deleteIptvMutation = useMutation({
    mutationFn: ({ sourceName, slug }: { sourceName: string; slug: string }) =>
      IptvPoolService.deleteEntry({ sourceName, slug }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["iptv_pool"] })
    },
  })

  const iptvEntries =
    iptvPoolData?.sources.flatMap((source) =>
      source.entries.map((entry) => ({
        ...entry,
        source_name: source.source_name,
      })),
    ) ?? []

  const hasEntries =
    acePoolData.ace_instances.length > 0 || iptvEntries.length > 0

  if (!hasEntries) {
    return null
  }

  return (
    <Box>
      <Heading size="xs" py={1}>
        Currently Loaded Streams
      </Heading>
      <AppTableRoot preset="outlineSm" maxW="fit-content">
        <TableHeader>
          <TableRow>
            <TableColumnHeader>Type</TableColumnHeader>
            <TableColumnHeader>Source</TableColumnHeader>
            <TableColumnHeader>Quality</TableColumnHeader>
            <TableColumnHeader>Status</TableColumnHeader>
            <TableColumnHeader>Currently Playing</TableColumnHeader>
            <TableColumnHeader>Make Available</TableColumnHeader>
          </TableRow>
        </TableHeader>
        <TableBody>
          {acePoolData.ace_instances.map((instance, index) => (
            <TableRow key={`ace-${instance.ace_pid}`}>
              <TableCell textAlign={"center"}>ace</TableCell>
              <TableCell textAlign={"center"}>ACE [{index + 1}]</TableCell>
              <AceInstanceQuality contentId={instance.content_id} />
              <TableCell textAlign={"center"}>
                {instance.locked_in
                  ? `🔒 Locked (${formatTime(instance.time_until_unlock ?? 0)})`
                  : "Available"}
              </TableCell>
              <AceInstanceTitle contentId={instance.content_id} />
              <TableCell textAlign={"center"}>
                {instance.locked_in ? (
                  <Link
                    colorPalette="red"
                    onClick={() =>
                      deleteAceMutation.mutate(instance.content_id)
                    }
                    cursor="pointer"
                  >
                    🔓 Unlock
                  </Link>
                ) : (
                  "-"
                )}
              </TableCell>
            </TableRow>
          ))}
          {iptvEntries.map((entry, index) => (
            <TableRow key={`iptv-${entry.source_name}-${entry.slug}`}>
              <TableCell textAlign={"center"}>iptv</TableCell>
              <TableCell textAlign={"center"}>
                {entry.source_name} [{index + 1}]
              </TableCell>
              <IptvInstanceQuality slug={entry.slug} />
              <TableCell textAlign={"center"}>
                {entry.locked_in
                  ? `🔒 Locked (${formatTime(entry.time_until_unlock_seconds)})`
                  : "Available"}
              </TableCell>
              <IptvInstanceTitle slug={entry.slug} />
              <TableCell textAlign={"center"}>
                {entry.locked_in ? (
                  <Link
                    colorPalette="red"
                    onClick={() =>
                      deleteIptvMutation.mutate({
                        sourceName: entry.source_name,
                        slug: entry.slug,
                      })
                    }
                    cursor="pointer"
                  >
                    🔓 Unlock
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
