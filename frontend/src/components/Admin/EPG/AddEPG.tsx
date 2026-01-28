import { Box, Heading, HStack, Text, Textarea, VStack } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type EPGInstanceConf_Input, EpgService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import { CodeBlock } from "@/components/ui/code"
import { Field } from "@/components/ui/field"
import { Link } from "@/components/ui/link"
import baseURL from "@/helpers"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { exampleEPGSource } from "./AddEPGExample"

const VITE_API_URL = baseURL()

function getEPGMappingQueryOptions() {
  return {
    queryFn: () => EpgService.tvgEpgMappings(),
    queryKey: ["resolvedEpgMappings"],
  }
}

function AddEPGJson() {
  const [jsonInput, setJsonInput] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data, isLoading } = useQuery({
    ...getEPGMappingQueryOptions(),
    placeholderData: (prevData) => prevData,
  })

  const mutation = useMutation({
    mutationFn: (data: EPGInstanceConf_Input) =>
      EpgService.addEpg({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("EPG source added successfully.")
      setJsonInput("")
      setIsSubmitting(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
      setIsSubmitting(false)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: [] })
    },
  })

  const handleSubmit = () => {
    if (!jsonInput.trim()) {
      showErrorToast("Please enter JSON data for the EPG source.")
      return
    }

    try {
      const parsedData = JSON.parse(jsonInput) as EPGInstanceConf_Input

      setIsSubmitting(true)
      mutation.mutate(parsedData)
    } catch {
      showErrorToast("Invalid JSON format. Please check your input.")
    }
  }

  if (isLoading) {
    return <Text>Loading...</Text>
  }

  const unmappedTvgIds = data
    ? Object.entries(data)
        .filter(([, epgId]) => epgId === null)
        .map(([tvgId]) => tvgId)
    : []

  return (
    <VStack align="start" gap={4}>
      <Heading size="md" mt={2} mb={1}>
        Streams without an EPG
      </Heading>

      {unmappedTvgIds.length > 0 && (
        <Box>
          <Text fontSize="sm" fontWeight="semibold" mb={2}>
            TVG IDs without mapped EPG ({unmappedTvgIds.length}):
          </Text>
          <CodeBlock>
            <VStack align="start" gap={0}>
              {unmappedTvgIds.map((tvgId) => (
                <Text key={tvgId} fontSize="xs" fontFamily="mono">
                  {tvgId}
                </Text>
              ))}
            </VStack>
          </CodeBlock>
        </Box>
      )}

      {unmappedTvgIds.length === 0 && (
        <Text fontSize="sm" color="gray.500">
          All TVG IDs have mapped EPGs.
        </Text>
      )}

      <Heading size="md" mt={2} mb={1}>
        Add EPG Source via JSON
      </Heading>
      <Text fontSize="sm">
        Enter the JSON configuration for your EPG source. Can also be done as a
        list. Refer to EPGInstanceConf in the{" "}
        <Link href={`${VITE_API_URL}/docs`}>API docs</Link> schemas for
        filtering information.
      </Text>
      <Field label="JSON Configuration" required>
        <CodeBlock>
          <Textarea
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
            placeholder="{}"
            rows={16}
            size="xs"
            resize="vertical"
          />
        </CodeBlock>
      </Field>
      <HStack gap={4} width="full">
        <Button
          size="xs"
          onClick={() =>
            setJsonInput(JSON.stringify(exampleEPGSource, null, 2))
          }
        >
          Load Example
        </Button>

        <Button
          size="xs"
          onClick={handleSubmit}
          loading={isSubmitting}
          loadingText="Adding..."
          colorPalette="teal"
        >
          Add EPG Source
        </Button>
      </HStack>
    </VStack>
  )
}

export default AddEPGJson
