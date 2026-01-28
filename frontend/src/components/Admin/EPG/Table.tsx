import { Box, Collapsible, Flex, Heading, VStack } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useState } from "react"
import { FaAngleDown, FaAngleUp } from "react-icons/fa"
import { EpgService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import { CodeBlock } from "@/components/ui/code"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

function getEPGQueryOptions() {
  return {
    queryFn: () => EpgService.getEpgs(),
    queryKey: ["epgInstances"],
  }
}

function EPGTable() {
  const queryClient = useQueryClient()
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({})
  const { showSuccessToast } = useCustomToast()

  const { data, isLoading } = useQuery({
    ...getEPGQueryOptions(),
    placeholderData: (prevData) => prevData,
  })

  const mutation = useMutation({
    mutationFn: (EPGSlug: string) => EpgService.deleteEpg({ slug: EPGSlug }),
    onSuccess: () => {
      showSuccessToast("Scraper source deleted successfully.")
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["epgInstances"] })
    },
  })

  const handleRemoveBySlug = useCallback(
    (slug: string) => {
      if (mutation.isPending) {
        return // Prevent multiple calls while one is in progress
      }
      console.log("Deleting stream with content ID:", slug)
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
    return <Box>Loading...</Box>
  }

  return (
    <>
      <Heading>EPG Management</Heading>
      <VStack align="start">
        {data?.map((epg) => (
          <Flex
            key={epg.slug}
            direction="column"
            p={2}
            borderWidth="1px"
            w="full"
          >
            <Collapsible.Root open={openItems[epg.slug] || false}>
              <Collapsible.Trigger
                cursor="pointer"
                onClick={() => toggleCollapsible(epg.slug)}
              >
                <Flex align="center" justify="space-between">
                  <Box p="1">
                    {openItems[epg.slug] ? <FaAngleUp /> : <FaAngleDown />}
                  </Box>
                  <Heading size="sm" mr={2}>
                    {epg.slug}
                  </Heading>
                </Flex>
              </Collapsible.Trigger>
              <Collapsible.Content>
                <CodeBlock whiteSpace="pre">
                  {JSON.stringify(epg, null, 2)}
                </CodeBlock>
                <Button
                  m={2}
                  size="xs"
                  onClick={() => handleRemoveBySlug(epg.slug)}
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

export default EPGTable
