import { Box, Heading, Text } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { StreamsService } from "@/client"

function getStreamQueryOptions(content_id: string) {
  return {
    queryFn: () => StreamsService.byContentId({ contentId: content_id }),
    queryKey: ["content_id", content_id],
  }
}

export function DynamicTitle() {
  const [contentId, setContentId] = useState(window.location.hash.substring(1))
  useEffect(() => {
    const handleHashChange = () => {
      setContentId(window.location.hash.substring(1))
    }

    window.addEventListener("hashchange", handleHashChange)
    return () => window.removeEventListener("hashchange", handleHashChange)
  }, [])

  const { data, isLoading, isPlaceholderData } = useQuery({
    ...getStreamQueryOptions(contentId),
    placeholderData: (prevData) => prevData,
    enabled: !!contentId, // Only run query when contentId exists
  })

  if (!data || isLoading || !contentId) {
    return (
      <Box>
        <Heading size="lg">No Stream Loaded</Heading>
        <Text>No Program Information</Text>
      </Box>
    )
  }

  return (
    <Box>
      <Heading opacity={isPlaceholderData ? 0.5 : 1}>{data.title}</Heading>
      <Text>
        {data.program_title ? data.program_title : "No Program Information"}
      </Text>
    </Box>
  )
}
