import {
  Heading,
  HStack,
  Portal,
  Select,
  Text,
  Textarea,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type AceScraperSourceApi, ScraperService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import { CodeBlock } from "@/components/ui/code"
import { Field } from "@/components/ui/field"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { jsonExamples } from "./AddScraperExamples"

function AddScraperJson() {
  const [jsonInput, setJsonInput] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: (data: AceScraperSourceApi) =>
      ScraperService.addSource({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Scraper source added successfully.")
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
      showErrorToast("Please enter JSON data for the scraper source.")
      return
    }

    try {
      const parsedData = JSON.parse(jsonInput) as AceScraperSourceApi

      setIsSubmitting(true)
      mutation.mutate(parsedData)
    } catch {
      showErrorToast("Invalid JSON format. Please check your input.")
    }
  }

  return (
    <VStack align="start" gap={4}>
      <Heading size="md">Add Scraper via JSON</Heading>

      <Text fontSize="sm">
        Enter the JSON configuration for your scraper source. Can also be done
        as a list.
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
        <Select.Root
          collection={jsonExamples}
          onValueChange={(details) => {
            if (details.items && details.items.length > 0) {
              const selectedItem = details.items[0]
              setJsonInput(selectedItem.value)
            }
          }}
          width="200px"
        >
          <Select.HiddenSelect />
          {/* <Select.Label>Load Example</Select.Label> */}
          <Select.Control>
            <Select.Trigger>
              <Select.ValueText placeholder="Load Example" />
            </Select.Trigger>
            <Select.IndicatorGroup>
              <Select.Indicator />
            </Select.IndicatorGroup>
          </Select.Control>
          <Portal>
            <Select.Positioner>
              <Select.Content>
                {jsonExamples.items.map((example) => (
                  <Select.Item item={example} key={example.key}>
                    {example.label}
                  </Select.Item>
                ))}
              </Select.Content>
            </Select.Positioner>
          </Portal>
        </Select.Root>

        <Button
          size="xs"
          onClick={handleSubmit}
          loading={isSubmitting}
          loadingText="Adding..."
          colorScheme="blue"
        >
          Add Scraper Source
        </Button>
      </HStack>
    </VStack>
  )
}
export default AddScraperJson
