import {
  Box,
  Heading,
  HStack,
  Input,
  NativeSelect,
  Table,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import type { IPTVStreamOverride } from "@/client"
import { IptvScraperService, IptvStreamsService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import { Field } from "@/components/ui/field"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface OverrideRow {
  streamTitle: string
  name: string
  category: string
  tvg_id: string
}

function StreamOverrides() {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const [selectedSource, setSelectedSource] = useState("")
  const [editState, setEditState] = useState<Record<string, OverrideRow>>({})
  const [newOverride, setNewOverride] = useState<OverrideRow | null>(null)

  const { data: sources } = useQuery({
    queryFn: () => IptvScraperService.sources(),
    queryKey: ["iptvScrapers"],
    placeholderData: (prevData) => prevData,
  })

  const { data: overrides, isLoading: overridesLoading } = useQuery({
    queryFn: () =>
      IptvScraperService.getStreamOverrides({ sourceName: selectedSource }),
    queryKey: ["iptvStreamOverrides", selectedSource],
    enabled: !!selectedSource,
    placeholderData: (prevData) => prevData,
  })

  const { data: streams } = useQuery({
    queryFn: () => IptvStreamsService.streams(),
    queryKey: ["iptvStreams"],
    enabled: !!selectedSource,
    placeholderData: (prevData) => prevData,
  })

  const availableTitles = useMemo(() => {
    if (!streams || !selectedSource) return []
    const overrideKeys = new Set(overrides ? Object.keys(overrides) : [])
    return streams
      .filter(
        (s) => s.source_name === selectedSource && !overrideKeys.has(s.title),
      )
      .map((s) => s.title)
      .sort()
  }, [streams, selectedSource, overrides])

  const saveMutation = useMutation({
    mutationFn: (data: {
      sourceName: string
      streamTitle: string
      override: IPTVStreamOverride
    }) =>
      IptvScraperService.setStreamOverride({
        sourceName: data.sourceName,
        streamTitle: data.streamTitle,
        requestBody: data.override,
      }),
    onSuccess: (_data, variables) => {
      showSuccessToast("Stream override saved.")
      setEditState((prev) => {
        const next = { ...prev }
        delete next[variables.streamTitle]
        return next
      })
      if (newOverride?.streamTitle === variables.streamTitle) {
        setNewOverride(null)
      }
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["iptvStreamOverrides", selectedSource],
      })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (data: { sourceName: string; streamTitle: string }) =>
      IptvScraperService.deleteStreamOverride({
        sourceName: data.sourceName,
        streamTitle: data.streamTitle,
      }),
    onSuccess: () => {
      showSuccessToast("Stream override deleted.")
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["iptvStreamOverrides", selectedSource],
      })
    },
  })

  const getEditRow = (
    streamTitle: string,
    original: IPTVStreamOverride,
  ): OverrideRow => {
    if (editState[streamTitle]) return editState[streamTitle]
    return {
      streamTitle,
      name: original.name ?? "",
      category: original.category ?? "",
      tvg_id: original.tvg_id ?? "",
    }
  }

  const updateEditField = (
    streamTitle: string,
    field: keyof Omit<OverrideRow, "streamTitle">,
    value: string,
    original: IPTVStreamOverride,
  ) => {
    const current = getEditRow(streamTitle, original)
    setEditState((prev) => ({
      ...prev,
      [streamTitle]: { ...current, [field]: value },
    }))
  }

  const handleSave = (row: OverrideRow) => {
    saveMutation.mutate({
      sourceName: selectedSource,
      streamTitle: row.streamTitle,
      override: {
        name: row.name,
        category: row.category,
        tvg_id: row.tvg_id,
      },
    })
  }

  const handleDelete = (streamTitle: string) => {
    if (deleteMutation.isPending) return
    deleteMutation.mutate({
      sourceName: selectedSource,
      streamTitle,
    })
  }

  const handleAddFromDropdown = (title: string) => {
    if (!title) return
    setNewOverride({
      streamTitle: title,
      name: "",
      category: "",
      tvg_id: "",
    })
  }

  const overrideEntries = overrides ? Object.entries(overrides) : []

  return (
    <VStack align="start" gap={4} w="full">
      <Heading size="md" mt={2} mb={1}>
        Stream Overrides
      </Heading>

      <Box w="full" maxW="400px">
        <Field label="IPTV Source">
          <NativeSelect.Root size="sm">
            <NativeSelect.Field
              value={selectedSource}
              onChange={(e) => {
                setSelectedSource(e.target.value)
                setEditState({})
                setNewOverride(null)
              }}
            >
              <option value="">Select a source...</option>
              {sources?.map((source) => (
                <option key={source.name} value={source.name}>
                  {source.name}
                </option>
              ))}
            </NativeSelect.Field>
            <NativeSelect.Indicator />
          </NativeSelect.Root>
        </Field>
      </Box>

      {selectedSource && overridesLoading && <Box>Loading...</Box>}

      {selectedSource && !overridesLoading && (
        <>
          {overrideEntries.length === 0 && !newOverride ? (
            <Box>No stream overrides configured for this source.</Box>
          ) : (
            <Table.Root size="sm" variant="outline" w="full">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>Original Title</Table.ColumnHeader>
                  <Table.ColumnHeader>Name Override</Table.ColumnHeader>
                  <Table.ColumnHeader>Category Override</Table.ColumnHeader>
                  <Table.ColumnHeader>TVG ID Override</Table.ColumnHeader>
                  <Table.ColumnHeader w="140px">Actions</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {overrideEntries.map(([streamTitle, override]) => {
                  const row = getEditRow(streamTitle, override)
                  return (
                    <Table.Row key={streamTitle}>
                      <Table.Cell fontSize="sm">{streamTitle}</Table.Cell>
                      <Table.Cell>
                        <Input
                          size="xs"
                          value={row.name}
                          placeholder="Name"
                          onChange={(e) =>
                            updateEditField(
                              streamTitle,
                              "name",
                              e.target.value,
                              override,
                            )
                          }
                        />
                      </Table.Cell>
                      <Table.Cell>
                        <Input
                          size="xs"
                          value={row.category}
                          placeholder="Category"
                          onChange={(e) =>
                            updateEditField(
                              streamTitle,
                              "category",
                              e.target.value,
                              override,
                            )
                          }
                        />
                      </Table.Cell>
                      <Table.Cell>
                        <Input
                          size="xs"
                          value={row.tvg_id}
                          placeholder="TVG ID"
                          onChange={(e) =>
                            updateEditField(
                              streamTitle,
                              "tvg_id",
                              e.target.value,
                              override,
                            )
                          }
                        />
                      </Table.Cell>
                      <Table.Cell>
                        <HStack gap={1}>
                          <Button
                            size="xs"
                            colorPalette="teal"
                            onClick={() => handleSave(row)}
                            loading={saveMutation.isPending}
                            disabled={!editState[streamTitle]}
                          >
                            Save
                          </Button>
                          <Button
                            size="xs"
                            colorPalette="red"
                            onClick={() => handleDelete(streamTitle)}
                            loading={deleteMutation.isPending}
                          >
                            Delete
                          </Button>
                        </HStack>
                      </Table.Cell>
                    </Table.Row>
                  )
                })}
                {newOverride && (
                  <Table.Row>
                    <Table.Cell fontSize="sm">
                      {newOverride.streamTitle}
                    </Table.Cell>
                    <Table.Cell>
                      <Input
                        size="xs"
                        value={newOverride.name}
                        placeholder="Name"
                        onChange={(e) =>
                          setNewOverride((prev) =>
                            prev ? { ...prev, name: e.target.value } : null,
                          )
                        }
                      />
                    </Table.Cell>
                    <Table.Cell>
                      <Input
                        size="xs"
                        value={newOverride.category}
                        placeholder="Category"
                        onChange={(e) =>
                          setNewOverride((prev) =>
                            prev ? { ...prev, category: e.target.value } : null,
                          )
                        }
                      />
                    </Table.Cell>
                    <Table.Cell>
                      <Input
                        size="xs"
                        value={newOverride.tvg_id}
                        placeholder="TVG ID"
                        onChange={(e) =>
                          setNewOverride((prev) =>
                            prev ? { ...prev, tvg_id: e.target.value } : null,
                          )
                        }
                      />
                    </Table.Cell>
                    <Table.Cell>
                      <HStack gap={1}>
                        <Button
                          size="xs"
                          colorPalette="teal"
                          onClick={() => handleSave(newOverride)}
                          loading={saveMutation.isPending}
                        >
                          Save
                        </Button>
                        <Button
                          size="xs"
                          colorPalette="gray"
                          variant="subtle"
                          onClick={() => setNewOverride(null)}
                        >
                          Cancel
                        </Button>
                      </HStack>
                    </Table.Cell>
                  </Table.Row>
                )}
              </Table.Body>
            </Table.Root>
          )}

          {!newOverride && availableTitles.length > 0 && (
            <Box w="full" maxW="400px">
              <Field label="Add Override for Stream">
                <NativeSelect.Root size="sm">
                  <NativeSelect.Field
                    value=""
                    onChange={(e) => handleAddFromDropdown(e.target.value)}
                  >
                    <option value="">Select a stream...</option>
                    {availableTitles.map((title) => (
                      <option key={title} value={title}>
                        {title}
                      </option>
                    ))}
                  </NativeSelect.Field>
                  <NativeSelect.Indicator />
                </NativeSelect.Root>
              </Field>
            </Box>
          )}
        </>
      )}
    </VStack>
  )
}

export default StreamOverrides
