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
import { Checkbox } from "@/components/ui/checkbox"
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
  const [enableEpgInput, setEnableEpgInput] = useState(true)
  const [enableAceInput, setEnableAceInput] = useState(true)

  const { data, isLoading } = useQuery({
    ...getRemoteConfigQueryOptions(),
    placeholderData: (prevData) => prevData,
  })

  useEffect(() => {
    setUrlInput(data?.url ?? "")
    if (data) {
      setEnableEpgInput(data.enable_epg)
      setEnableAceInput(data.enable_ace)
    }
  }, [data])

  const mutation = useMutation({
    mutationFn: (requestBody: {
      url: string | null
      enable_epg: boolean
      enable_ace: boolean
    }) => ConfigService.triggerFetchRemoteSettings({ requestBody }),
    onSuccess: async () => {
      showSuccessToast("Remote settings updated successfully.")
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

    mutation.mutate({
      url: trimmedUrl,
      enable_epg: enableEpgInput,
      enable_ace: enableAceInput,
    })
  }

  const handleClearUrl = () => {
    mutation.mutate({
      url: null,
      enable_epg: enableEpgInput,
      enable_ace: enableAceInput,
    })
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
                Enable EPG:
              </Text>
              <Text>{data?.enable_epg ? "Enabled" : "Disabled"}</Text>
            </HStack>
            <HStack>
              <Text fontWeight="medium" minWidth="120px">
                Enable Ace:
              </Text>
              <Text>{data?.enable_ace ? "Enabled" : "Disabled"}</Text>
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

        <HStack gap={6}>
          <Checkbox
            checked={enableEpgInput}
            onCheckedChange={({ checked }) => setEnableEpgInput(!!checked)}
          >
            Enable EPG sync
          </Checkbox>
          <Checkbox
            checked={enableAceInput}
            onCheckedChange={({ checked }) => setEnableAceInput(!!checked)}
          >
            Enable Ace sync
          </Checkbox>
        </HStack>

        <HStack>
          <Button
            onClick={handleSetUrl}
            disabled={mutation.isPending || !urlInput.trim()}
            loading={mutation.isPending}
          >
            Save Remote Settings
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
