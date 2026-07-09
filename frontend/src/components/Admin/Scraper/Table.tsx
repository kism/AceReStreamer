import { Heading, VStack } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback } from "react"
import { ScraperService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import { Code, CodeBlock } from "@/components/ui/code"
import { CollapsibleSection } from "@/components/ui/collapsible-section"
import { Loading } from "@/components/ui/loading"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import ScraperFormDialog from "./ScraperFormDialog"

function ScraperTable() {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const { data, isLoading } = useQuery({
    queryFn: () => ScraperService.sources(),
    queryKey: ["scrapers"],
    placeholderData: (prevData) => prevData,
  })

  const mutation = useMutation({
    mutationFn: (slug: string) => ScraperService.removeSource({ slug: slug }),
    onSuccess: () => {
      showSuccessToast("Scraper source deleted successfully.")
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["scrapers"] })
    },
  })

  const handleRemoveBySlug = useCallback(
    (slug: string) => {
      if (mutation.isPending) {
        return // Prevent multiple calls while one is in progress
      }
      mutation.mutate(slug)
    },
    [mutation],
  )

  if (isLoading) {
    return <Loading />
  }

  return (
    <>
      <Heading size="md" mt={2} mb={1}>
        Scraper List
      </Heading>
      <VStack align="start">
        {data?.map((scraper) => (
          <CollapsibleSection
            key={scraper.name}
            title={scraper.name}
            headerExtra={() => <Code>{scraper.type}</Code>}
          >
            <CodeBlock whiteSpace="pre">
              {JSON.stringify(scraper, null, 2)}
            </CodeBlock>
            <ScraperFormDialog
              existing={scraper}
              trigger={
                <Button m={2} size="xs" colorPalette="teal">
                  Edit
                </Button>
              }
            />
            <Button
              m={2}
              size="xs"
              colorPalette="red"
              onClick={() => handleRemoveBySlug(scraper.name)}
            >
              Delete
            </Button>
          </CollapsibleSection>
        ))}
      </VStack>
    </>
  )
}

export default ScraperTable
