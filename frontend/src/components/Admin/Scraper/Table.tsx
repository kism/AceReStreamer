import {
  Box,
  Button,
  Collapsible,
  Flex,
  Heading,
  VStack,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useState } from "react"
import { FaAngleDown, FaAngleUp } from "react-icons/fa"
import { ScraperService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { Code, CodeBlock } from "@/components/ui/code"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

function getScrapersQueryOptions() {
  return {
    queryFn: () => ScraperService.sources(),
    queryKey: ["scrapers"],
  }
}

function ScraperTable() {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({})

  const { data, isLoading } = useQuery({
    ...getScrapersQueryOptions(),
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

  const toggleCollapsible = useCallback((name: string) => {
    setOpenItems((prev) => ({
      ...prev,
      [name]: !prev[name],
    }))
  }, [])

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <>
      <Heading size="md" py={4}>
        Scraper List
      </Heading>
      <VStack align="start">
        {data?.map((scraper) => (
          <Flex
            key={scraper.name}
            direction="column"
            p={2}
            borderWidth="1px"
            //   borderRadius="md"
            w="full"
          >
            <Collapsible.Root open={openItems[scraper.name] || false}>
              <Collapsible.Trigger
                cursor="pointer"
                onClick={() => toggleCollapsible(scraper.name)}
              >
                <Flex align="center" justify="space-between">
                  <Box p="1">
                    {openItems[scraper.name] ? <FaAngleUp /> : <FaAngleDown />}
                  </Box>
                  <Heading size="sm" mr={2}>
                    {scraper.name}
                  </Heading>
                  <Code>{scraper.type}</Code>
                </Flex>
              </Collapsible.Trigger>
              <Collapsible.Content>
                <CodeBlock whiteSpace="pre">
                  {JSON.stringify(scraper, null, 2)}
                </CodeBlock>
                <Button
                  m={2}
                  size="xs"
                  onClick={() => handleRemoveBySlug(scraper.name)}
                >
                  Delete
                </Button>
              </Collapsible.Content>
            </Collapsible.Root>
          </Flex>
        ))}
      </VStack>
    </>
  )
}

export default ScraperTable
