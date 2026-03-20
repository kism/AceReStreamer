import { Box, Collapsible, Flex, Heading, VStack } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useState } from "react"
import { FaAngleDown, FaAngleUp } from "react-icons/fa"
import { IptvScraperService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import { Code, CodeBlock } from "@/components/ui/code"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

function getIptvScrapersQueryOptions() {
  return {
    queryFn: () => IptvScraperService.sources(),
    queryKey: ["iptvScrapers"],
  }
}

function IptvScraperTable() {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({})

  const { data, isLoading } = useQuery({
    ...getIptvScrapersQueryOptions(),
    placeholderData: (prevData) => prevData,
  })

  const mutation = useMutation({
    mutationFn: (sourceName: string) =>
      IptvScraperService.removeSource({ sourceName }),
    onSuccess: () => {
      showSuccessToast("IPTV source deleted successfully.")
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["iptvScrapers"] })
    },
  })

  const handleRemoveByName = useCallback(
    (name: string) => {
      if (mutation.isPending) {
        return
      }
      mutation.mutate(name)
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
      <Heading size="md" mt={2} mb={1}>
        IPTV Source List
      </Heading>
      <VStack align="start">
        {data?.map((source) => (
          <Flex
            key={source.name}
            direction="column"
            p={2}
            borderWidth="1px"
            w="full"
          >
            <Collapsible.Root open={openItems[source.name] || false}>
              <Collapsible.Trigger
                cursor="pointer"
                onClick={() => toggleCollapsible(source.name)}
              >
                <Flex align="center" justify="space-between">
                  <Box p="1">
                    {openItems[source.name] ? <FaAngleUp /> : <FaAngleDown />}
                  </Box>
                  <Heading size="sm" mr={2}>
                    {source.name}
                  </Heading>
                  <Code>{source.type}</Code>
                </Flex>
              </Collapsible.Trigger>
              <Collapsible.Content>
                <CodeBlock whiteSpace="pre">
                  {JSON.stringify(source, null, 2)}
                </CodeBlock>
                <Button
                  m={2}
                  size="xs"
                  colorPalette="red"
                  onClick={() => handleRemoveByName(source.name)}
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

export default IptvScraperTable
