import {
  Box,
  Code,
  Heading,
  HStack,
  Input,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { ConfigService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import { CodeBlock } from "@/components/ui/code"
import { Field } from "@/components/ui/field"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

function getRemoteConfigQueryOptions() {
  return {
    queryFn: () => ConfigService.fetchRemoteSettings(),
    queryKey: ["remoteConfig"],
  }
}

function RemoteConfig() {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [urlInput, setUrlInput] = useState("")

  const { data, isLoading } = useQuery({
    ...getRemoteConfigQueryOptions(),
    placeholderData: (prevData) => prevData,
  })

  useEffect(() => {
    if (data?.url) {
      setUrlInput(data.url)
    }
  }, [data?.url])

  const mutation = useMutation({
    mutationFn: (url: string | null) =>
      ConfigService.triggerFetchRemoteSettings({ requestBody: { url } }),
    onSuccess: async () => {
      showSuccessToast("Remote settings URL updated successfully.")
      setUrlInput("")
      // Refresh after successful update
      await queryClient.invalidateQueries({ queryKey: ["remoteConfig"] })
      await queryClient.invalidateQueries({ queryKey: ["config"] })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })

  const handleRefresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["remoteConfig"] })
  }

  const handleSetUrl = () => {
    const trimmedUrl = urlInput.trim()
    if (!trimmedUrl) {
      showErrorToast("Please enter a URL.")
      return
    }

    mutation.mutate(trimmedUrl)
  }

  const handleClearUrl = () => {
    mutation.mutate(null)
  }

  if (isLoading) {
    return <Box>Loading...</Box>
  }

  return (
    <VStack align="start" gap={4} width="100%">
      <Box>
        <Heading size="md">Remote Configuration</Heading>
        <Text fontSize="sm" color="fg.muted">
          Configure a remote URL to automatically fetch epg and scraper
          configuration from.
        </Text>
      </Box>

      {/* Current Configuration Readout */}
      <VStack align="start" gap={2} width="100%">
        <Heading size="sm">Current Configuration</Heading>
        <Box width="100%" p={1} borderWidth="1px">
          <VStack align="start" gap={0} width="100%">
            <HStack>
              <Text fontWeight="medium" minWidth="120px">
                URL:
              </Text>
              <Code color={data?.url ? "fg.default" : "fg.muted"}>
                {data?.url || "Not configured"}
              </Code>
            </HStack>
            <HStack>
              <Text fontWeight="medium" minWidth="120px">
                Status:
              </Text>
              <Text>{data?.status || "N/A"}</Text>
            </HStack>
            <HStack>
              <Text fontWeight="medium" minWidth="120px">
                Last Fetched:
              </Text>
              <Text color={data?.last_fetched ? "fg.default" : "fg.muted"}>
                {data?.last_fetched
                  ? new Date(data.last_fetched).toLocaleString()
                  : "Never"}
              </Text>
            </HStack>
          </VStack>
        </Box>
        {data?.url && (
          <Button size="xs" onClick={handleRefresh} disabled={isLoading}>
            Refresh Information
          </Button>
        )}
      </VStack>
      {/* Set Remote Configuration URL */}
      <VStack align="start" gap={3} width="100%">
        <Heading size="sm">Set Remote Configuration URL</Heading>
        <Field label="Remote URL" width="full">
          <CodeBlock>
            <Input
              size="xs"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://example.com/config.json"
              disabled={mutation.isPending}
            />
          </CodeBlock>
        </Field>

        <HStack>
          <Button
            onClick={handleSetUrl}
            disabled={mutation.isPending || !urlInput.trim()}
            loading={mutation.isPending}
          >
            Set URL
          </Button>
          {data?.url && (
            <Button
              colorPalette="red"
              onClick={handleClearUrl}
              disabled={mutation.isPending}
            >
              Clear
            </Button>
          )}
        </HStack>
      </VStack>
    </VStack>
  )
}

export default RemoteConfig
