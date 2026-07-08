import {
  Box,
  createListCollection,
  HStack,
  Input,
  Select,
  SimpleGrid,
  Textarea,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { FaRegQuestionCircle } from "react-icons/fa"
import { type AceScraperSourceApi, ScraperService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DialogActionTrigger,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Field } from "@/components/ui/field"
import { Tooltip } from "@/components/ui/tooltip"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

type ScraperType = AceScraperSourceApi["type"]

const scraperTypes = createListCollection({
  items: [
    { label: "HTML page", value: "html" },
    { label: "IPTV m3u8 playlist", value: "iptv" },
    { label: "JSON API", value: "api" },
  ],
})

const helpText = {
  type: "HTML page: scrape acestream:// links from a web page. IPTV m3u8 playlist: import streams from an IPTV playlist. JSON API: import streams from a JSON API endpoint.",
  name: "Unique name for this source (will be slugified). Leave blank to derive it from the URL.",
  url: "The web page, m3u8 playlist, or API endpoint to scrape.",
  always_exclude_words:
    "One per line. Stream titles containing any of these words are always excluded. Evaluated first.",
  always_include_words:
    "One per line. Stream titles containing any of these words are always included (unless always-excluded).",
  exclude_words:
    "One per line. Stream titles containing any of these words are excluded.",
  include_words:
    "One per line. If set, only stream titles containing one of these words are included. Empty allows all.",
  regex_postprocessing:
    "One per line. Regex patterns removed from stream titles via re.sub after filtering.",
  target_class:
    "HTML class of the elements to search within for acestream links.",
  check_sibling:
    "Also check sibling elements of the matched elements for stream names.",
}

function HelpTip({ text }: { text: string }) {
  return (
    <Tooltip content={text} showArrow>
      <Box
        as="span"
        display="inline-flex"
        tabIndex={0}
        color="fg.muted"
        cursor="help"
      >
        <FaRegQuestionCircle size={12} />
      </Box>
    </Tooltip>
  )
}

function labelWithHelp(label: string, help: string) {
  return (
    <HStack gap={1}>
      {label}
      <HelpTip text={help} />
    </HStack>
  )
}

interface FormState {
  type: ScraperType | ""
  name: string
  url: string
  always_exclude_words: string
  always_include_words: string
  exclude_words: string
  include_words: string
  regex_postprocessing: string
  target_class: string
  check_sibling: boolean
}

function initialFormState(existing?: AceScraperSourceApi): FormState {
  return {
    type: existing?.type ?? "",
    name: existing?.name ?? "",
    url: existing?.url ?? "",
    always_exclude_words: (
      existing?.title_filter?.always_exclude_words ?? []
    ).join("\n"),
    always_include_words: (
      existing?.title_filter?.always_include_words ?? []
    ).join("\n"),
    exclude_words: (existing?.title_filter?.exclude_words ?? []).join("\n"),
    include_words: (existing?.title_filter?.include_words ?? []).join("\n"),
    regex_postprocessing: (
      existing?.title_filter?.regex_postprocessing ?? []
    ).join("\n"),
    target_class: existing?.html_filter?.target_class ?? "",
    check_sibling: existing?.html_filter?.check_sibling ?? false,
  }
}

function linesToList(value: string): string[] {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
}

interface ScraperFormDialogProps {
  existing?: AceScraperSourceApi
  trigger: React.ReactNode
}

function ScraperFormDialog({ existing, trigger }: ScraperFormDialogProps) {
  const [open, setOpen] = useState(false)
  const [formData, setFormData] = useState<FormState>(() =>
    initialFormState(existing),
  )
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: (data: AceScraperSourceApi) =>
      existing
        ? ScraperService.updateSource({
            slug: existing.name,
            requestBody: data,
          })
        : ScraperService.addSource({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast(
        existing
          ? "Scraper source updated successfully."
          : "Scraper source added successfully.",
      )
      setOpen(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["scrapers"] })
    },
  })

  const handleInputChange =
    (field: keyof FormState) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setFormData((prev) => ({ ...prev, [field]: e.target.value }))
    }

  const handleSubmit = () => {
    if (formData.type === "") {
      return
    }
    if (!formData.url.trim()) {
      showErrorToast("Please fill in the URL.")
      return
    }

    const requestBody: AceScraperSourceApi = {
      type: formData.type,
      name: formData.name.trim(),
      url: formData.url.trim(),
      title_filter: {
        always_exclude_words: linesToList(formData.always_exclude_words),
        always_include_words: linesToList(formData.always_include_words),
        exclude_words: linesToList(formData.exclude_words),
        include_words: linesToList(formData.include_words),
        regex_postprocessing: linesToList(formData.regex_postprocessing),
      },
      html_filter:
        formData.type === "html"
          ? {
              target_class: formData.target_class.trim(),
              check_sibling: formData.check_sibling,
            }
          : null,
    }

    mutation.mutate(requestBody)
  }

  return (
    <DialogRoot
      open={open}
      onOpenChange={(e) => {
        setOpen(e.open)
        if (e.open) {
          setFormData(initialFormState(existing))
        }
      }}
      size="lg"
      scrollBehavior="inside"
    >
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {existing
              ? `Edit Scraper Source: ${existing.name}`
              : "Add Scraper Source"}
          </DialogTitle>
        </DialogHeader>
        <DialogCloseTrigger />
        <DialogBody>
          <VStack align="stretch" gap={3}>
            <Field
              label={labelWithHelp("Scraper Type", helpText.type)}
              required
            >
              <Select.Root
                collection={scraperTypes}
                value={formData.type ? [formData.type] : []}
                onValueChange={(details) => {
                  const value = details.value[0] as ScraperType | undefined
                  if (value) {
                    setFormData((prev) => ({ ...prev, type: value }))
                  }
                }}
                size="sm"
              >
                <Select.HiddenSelect />
                <Select.Control>
                  <Select.Trigger>
                    <Select.ValueText placeholder="Select a scraper type" />
                  </Select.Trigger>
                  <Select.IndicatorGroup>
                    <Select.Indicator />
                  </Select.IndicatorGroup>
                </Select.Control>
                <Select.Positioner>
                  <Select.Content>
                    {scraperTypes.items.map((item) => (
                      <Select.Item item={item} key={item.value}>
                        {item.label}
                      </Select.Item>
                    ))}
                  </Select.Content>
                </Select.Positioner>
              </Select.Root>
            </Field>

            {formData.type !== "" && (
              <>
                <SimpleGrid columns={{ base: 1, md: 2 }} gap={3}>
                  <Field label={labelWithHelp("Name", helpText.name)}>
                    <Input
                      value={formData.name}
                      onChange={handleInputChange("name")}
                      placeholder="My Scraper"
                      size="sm"
                    />
                  </Field>

                  <Field label={labelWithHelp("URL", helpText.url)} required>
                    <Input
                      value={formData.url}
                      onChange={handleInputChange("url")}
                      placeholder="https://example.com"
                      size="sm"
                    />
                  </Field>
                </SimpleGrid>

                {formData.type === "html" && (
                  <SimpleGrid columns={{ base: 1, md: 2 }} gap={3}>
                    <Field
                      label={labelWithHelp(
                        "Target Class",
                        helpText.target_class,
                      )}
                    >
                      <Input
                        value={formData.target_class}
                        onChange={handleInputChange("target_class")}
                        placeholder="linklist"
                        size="sm"
                      />
                    </Field>

                    <Field
                      label={labelWithHelp(
                        "Check Sibling",
                        helpText.check_sibling,
                      )}
                    >
                      <Checkbox
                        checked={formData.check_sibling}
                        onCheckedChange={(details) => {
                          setFormData((prev) => ({
                            ...prev,
                            check_sibling: details.checked === true,
                          }))
                        }}
                      />
                    </Field>
                  </SimpleGrid>
                )}

                <SimpleGrid columns={{ base: 1, md: 2 }} gap={3}>
                  <Field
                    label={labelWithHelp(
                      "Always Exclude Words",
                      helpText.always_exclude_words,
                    )}
                  >
                    <Textarea
                      value={formData.always_exclude_words}
                      onChange={handleInputChange("always_exclude_words")}
                      placeholder={"one\nper\nline"}
                      rows={3}
                      size="sm"
                    />
                  </Field>

                  <Field
                    label={labelWithHelp(
                      "Always Include Words",
                      helpText.always_include_words,
                    )}
                  >
                    <Textarea
                      value={formData.always_include_words}
                      onChange={handleInputChange("always_include_words")}
                      placeholder={"one\nper\nline"}
                      rows={3}
                      size="sm"
                    />
                  </Field>

                  <Field
                    label={labelWithHelp(
                      "Exclude Words",
                      helpText.exclude_words,
                    )}
                  >
                    <Textarea
                      value={formData.exclude_words}
                      onChange={handleInputChange("exclude_words")}
                      placeholder={"one\nper\nline"}
                      rows={3}
                      size="sm"
                    />
                  </Field>

                  <Field
                    label={labelWithHelp(
                      "Include Words",
                      helpText.include_words,
                    )}
                  >
                    <Textarea
                      value={formData.include_words}
                      onChange={handleInputChange("include_words")}
                      placeholder={"one\nper\nline"}
                      rows={3}
                      size="sm"
                    />
                  </Field>
                </SimpleGrid>

                <Field
                  label={labelWithHelp(
                    "Regex Postprocessing",
                    helpText.regex_postprocessing,
                  )}
                >
                  <Textarea
                    value={formData.regex_postprocessing}
                    onChange={handleInputChange("regex_postprocessing")}
                    placeholder={"\\[.*\\]"}
                    rows={3}
                    size="sm"
                  />
                </Field>
              </>
            )}
          </VStack>
        </DialogBody>
        <DialogFooter>
          <DialogActionTrigger asChild>
            <Button size="xs" variant="subtle">
              Cancel
            </Button>
          </DialogActionTrigger>
          <Button
            size="xs"
            colorPalette="teal"
            onClick={handleSubmit}
            disabled={formData.type === ""}
            loading={mutation.isPending}
            loadingText={existing ? "Saving..." : "Adding..."}
          >
            {existing ? "Save" : "Add"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </DialogRoot>
  )
}

export default ScraperFormDialog
