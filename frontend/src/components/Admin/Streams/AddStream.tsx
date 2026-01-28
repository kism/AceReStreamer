import { Box, Heading, HStack, Input, SimpleGrid, Text } from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type ManuallyAddedAceStream, StreamsService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

function AddStream() {
  const [formData, setFormData] = useState<ManuallyAddedAceStream>({
    title: "",
    content_id: "",
    tvg_id: "",
    group_title: "",
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: (data: ManuallyAddedAceStream) =>
      StreamsService.addStream({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Stream added successfully.")
      setFormData({
        title: "",
        content_id: "",
        tvg_id: "",
        group_title: "",
      })
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
    if (
      !formData.title.trim() ||
      !formData.content_id.trim() ||
      !formData.tvg_id.trim() ||
      !formData.group_title.trim()
    ) {
      showErrorToast("Please fill in all required fields.")
      return
    }

    setIsSubmitting(true)
    mutation.mutate(formData)
  }

  const handleInputChange =
    (field: keyof ManuallyAddedAceStream) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setFormData((prev) => ({ ...prev, [field]: e.target.value }))
    }

  return (
    <Box>
      <HStack justify="space-between" align="center" mb={3}>
        <Heading size="md" mt={2} mb={1}>
          Manually Add Stream
        </Heading>
      </HStack>

      <Box bg="orange.50" borderRadius="md" p={2} mb={3}>
        <Text fontSize="xs" color="orange.800">
          <strong>Warning:</strong> Scraped streams will override manual
          entries.
        </Text>
      </Box>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={3}>
        <Field label="Title" required>
          <Input
            value={formData.title}
            onChange={handleInputChange("title")}
            placeholder="Channel 1"
            size="xs"
          />
        </Field>

        <Field label="Ace Content ID" required>
          <Input
            value={formData.content_id}
            onChange={handleInputChange("content_id")}
            placeholder="40 character content ID"
            size="xs"
          />
        </Field>

        <Field label="TVG ID" required>
          <Input
            value={formData.tvg_id}
            onChange={handleInputChange("tvg_id")}
            placeholder="Channel 1.au"
            size="xs"
          />
        </Field>

        <Field label="Group Title" required>
          <Input
            value={formData.group_title}
            onChange={handleInputChange("group_title")}
            placeholder="General"
            size="xs"
          />
        </Field>

        <Button
          size="xs"
          maxW="150px"
          onClick={handleSubmit}
          loading={isSubmitting}
          loadingText="Adding..."
          colorPalette="teal"
        >
          Add Stream
        </Button>
      </SimpleGrid>
    </Box>
  )
}

export default AddStream
