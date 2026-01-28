import { Box, Heading, HStack, Input, Table, VStack } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { ScraperService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

function getNameOverridesQueryOptions() {
  return {
    queryFn: () => ScraperService.getNameOverrides(),
    queryKey: ["nameOverrides"],
  }
}

function NameOverrides() {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const [contentId, setContentId] = useState("")
  const [name, setName] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { data, isLoading } = useQuery({
    ...getNameOverridesQueryOptions(),
    placeholderData: (prevData) => prevData,
  })

  const addMutation = useMutation({
    mutationFn: (data: { contentId: string; name: string }) =>
      ScraperService.addNameOverride({
        contentId: data.contentId,
        name: data.name,
      }),
    onSuccess: () => {
      showSuccessToast("Name override added successfully.")
      setContentId("")
      setName("")
      setIsSubmitting(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
      setIsSubmitting(false)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["nameOverrides"] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (contentId: string) =>
      ScraperService.deleteNameOverride({ contentId }),
    onSuccess: () => {
      showSuccessToast("Name override deleted successfully.")
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["nameOverrides"] })
    },
  })

  const handleAddOverride = () => {
    if (!contentId.trim() || !name.trim()) {
      return
    }
    setIsSubmitting(true)
    addMutation.mutate({ contentId: contentId.trim(), name: name.trim() })
  }

  const handleDelete = (contentId: string) => {
    if (deleteMutation.isPending) {
      return
    }
    deleteMutation.mutate(contentId)
  }

  const overrideEntries = data ? Object.entries(data) : []

  return (
    <VStack align="start" gap={4} w="full">
      <Heading size="md" mt={2} mb={1}>
        Name Overrides
      </Heading>

      <Box w="full">
        <Field label="Add Name Override">
          <HStack gap={2} w="full">
            <Input
              placeholder="Content ID"
              value={contentId}
              onChange={(e) => setContentId(e.target.value)}
              disabled={isSubmitting}
            />
            <Input
              placeholder="Override Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isSubmitting}
            />
            <Button
              onClick={handleAddOverride}
              loading={isSubmitting}
              disabled={!contentId.trim() || !name.trim()}
            >
              Add
            </Button>
          </HStack>
        </Field>
      </Box>

      {isLoading ? (
        <Box>Loading...</Box>
      ) : overrideEntries.length === 0 ? (
        <Box>No name overrides configured.</Box>
      ) : (
        <Table.Root size="sm" variant="outline" w="full">
          <Table.Header>
            <Table.Row>
              <Table.ColumnHeader>Content ID</Table.ColumnHeader>
              <Table.ColumnHeader>Override Name</Table.ColumnHeader>
              <Table.ColumnHeader w="100px">Actions</Table.ColumnHeader>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {overrideEntries.map(([contentId, overrideName]) => (
              <Table.Row key={contentId}>
                <Table.Cell fontFamily="mono" fontSize="sm">
                  {contentId}
                </Table.Cell>
                <Table.Cell>{overrideName}</Table.Cell>
                <Table.Cell>
                  <Button
                    size="xs"
                    colorPalette="red"
                    onClick={() => handleDelete(contentId)}
                    loading={deleteMutation.isPending}
                  >
                    Delete
                  </Button>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Root>
      )}
    </VStack>
  )
}

export default NameOverrides
