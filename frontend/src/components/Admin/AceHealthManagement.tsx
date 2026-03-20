import {
  Box,
  Collapsible,
  Flex,
  Heading,
  HStack,
  VStack,
} from "@chakra-ui/react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useMemo, useState } from "react"
import { FaAngleDown, FaAngleUp } from "react-icons/fa"
import { AcePoolService, AceStreamsService } from "@/client"
import { Button } from "@/components/ui/button"
import { CodeBlock } from "@/components/ui/code"

function AceHealthManagement() {
  const queryClient = useQueryClient()
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({})
  const [streamCheckResult, setStreamCheckResult] = useState<unknown>(null)
  const [isCheckingStreams, setIsCheckingStreams] = useState(false)

  const { data: acePoolData, isLoading: isLoadingAcePool } = useQuery({
    queryKey: ["health", "acePool"],
    queryFn: () => AcePoolService.pool(),
  })

  const { data: acePoolStats, isLoading: isLoadingAcePoolStats } = useQuery({
    queryKey: ["health", "acePoolStats"],
    queryFn: () => AcePoolService.stats(),
  })

  const healthSections = useMemo(
    () => [
      {
        key: "acePool",
        title: "Ace Pool",
        data: acePoolData,
        isLoading: isLoadingAcePool,
        queryKey: ["health", "acePool"],
      },
      {
        key: "acePoolStats",
        title: "Ace Pool Stats",
        data: acePoolStats,
        isLoading: isLoadingAcePoolStats,
        queryKey: ["health", "acePoolStats"],
      },
    ],
    [acePoolData, acePoolStats, isLoadingAcePool, isLoadingAcePoolStats],
  )

  const isLoading = healthSections.some((section) => section.isLoading)

  const toggleCollapsible = useCallback((name: string) => {
    setOpenItems((prev) => ({
      ...prev,
      [name]: !prev[name],
    }))
  }, [])

  const handleRefresh = useCallback(
    (queryKey: string[]) => {
      queryClient.invalidateQueries({ queryKey })
    },
    [queryClient],
  )

  const handleStreamCheck = useCallback(async () => {
    setIsCheckingStreams(true)
    try {
      const data = await AceStreamsService.check()
      setStreamCheckResult(data)
    } catch (error) {
      setStreamCheckResult({ error: String(error) })
    } finally {
      setIsCheckingStreams(false)
    }
  }, [])

  if (isLoading) {
    return <Box>Loading...</Box>
  }

  return (
    <VStack align="start" width="100%">
      <Box>
        <Heading size="md">Ace Health Status</Heading>
      </Box>

      <Flex gap={4}>
        <VStack align="start" gap={2}>
          <HStack>
            <Button
              size="xs"
              onClick={handleStreamCheck}
              loading={isCheckingStreams}
            >
              Check Streams
            </Button>
            {streamCheckResult !== null && (
              <CodeBlock fontSize="2xs" whiteSpace="pre" flex={1}>
                {JSON.stringify(streamCheckResult, null)}
              </CodeBlock>
            )}
          </HStack>
        </VStack>
      </Flex>

      <VStack align="start" gap={4} width="100%">
        {healthSections.map((section) => (
          <Flex
            key={section.key}
            direction="column"
            p={2}
            borderWidth="1px"
            w="full"
          >
            <Collapsible.Root open={openItems[section.key] || false}>
              <Collapsible.Trigger
                cursor="pointer"
                onClick={() => toggleCollapsible(section.key)}
              >
                <Flex align="center" gap={2}>
                  <Box p="1">
                    {openItems[section.key] ? <FaAngleUp /> : <FaAngleDown />}
                  </Box>
                  <Heading size="sm">{section.title}</Heading>
                  {openItems[section.key] && (
                    <Button
                      size="2xs"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleRefresh(section.queryKey)
                      }}
                    >
                      Refresh
                    </Button>
                  )}
                </Flex>
              </Collapsible.Trigger>
              <Collapsible.Content>
                <CodeBlock fontSize={"2xs"} whiteSpace="pre">
                  {JSON.stringify(section.data, null, 2)}
                </CodeBlock>
              </Collapsible.Content>
            </Collapsible.Root>
          </Flex>
        ))}
      </VStack>
    </VStack>
  )
}

export default AceHealthManagement
