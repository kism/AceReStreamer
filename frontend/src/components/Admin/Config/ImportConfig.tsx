import { Heading, HStack, Text, Textarea, VStack } from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type ConfigExport_Input, ConfigService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import { CodeBlock } from "@/components/ui/code"
import { Field } from "@/components/ui/field"
import { Link } from "@/components/ui/link"
import baseURL from "@/helpers"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const VITE_API_URL = baseURL()

function ImportConfig() {
  const [jsonInput, setJsonInput] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: (data: ConfigExport_Input) =>
      ConfigService.updateConfig({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Configuration imported successfully.")
      setJsonInput("")
      setIsSubmitting(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
      setIsSubmitting(false)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["config"] })
      queryClient.invalidateQueries({ queryKey: [] })
    },
  })

  const handleSubmit = () => {
    if (!jsonInput.trim()) {
      showErrorToast("Please enter JSON configuration data.")
      return
    }

    try {
      const parsedData = JSON.parse(jsonInput) as ConfigExport_Input

      // Validate that the required fields exist
      if (!parsedData.scraper || !parsedData.epgs) {
        showErrorToast(
          "Invalid configuration format. Must include 'scraper' and 'epgs' fields.",
        )
        return
      }

      setIsSubmitting(true)
      mutation.mutate(parsedData)
    } catch {
      showErrorToast("Invalid JSON format. Please check your input.")
    }
  }

  return (
    <VStack align="start" gap={4}>
      <Heading size="md">Import Configuration</Heading>
      <Text fontSize="sm">
        Import a configuration to update your scraper and EPG settings. This
        will replace the existing scraper and EPG configurations. Refer to
        ConfigExport in the <Link href={`${VITE_API_URL}/docs`}>API docs</Link>{" "}
        for the expected format.
      </Text>

      <Field label="JSON Configuration" required>
        <CodeBlock>
          <Textarea
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
            placeholder='{"scraper": {...}, "epgs": [...]}'
            rows={16}
            size="xs"
            resize="vertical"
          />
        </CodeBlock>
      </Field>

      <HStack gap={4} width="full">
        <Button
          size="xs"
          onClick={handleSubmit}
          loading={isSubmitting}
          loadingText="Importing..."
          colorPalette="teal"
          disabled={!jsonInput.trim()}
        >
          Import Configuration
        </Button>
      </HStack>
    </VStack>
  )
}

export default ImportConfig
