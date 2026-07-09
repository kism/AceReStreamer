import { Box, Flex, Heading, HStack, VStack } from "@chakra-ui/react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useMemo, useState } from "react"
import {
  AcePoolService,
  ConfigService,
  HealthService,
  StreamsService,
} from "@/client"
import { Button } from "@/components/ui/button"
import { CodeBlock } from "@/components/ui/code"
import { CollapsibleSection } from "@/components/ui/collapsible-section"
import { Loading } from "@/components/ui/loading"

function HealthManagement() {
  const queryClient = useQueryClient()
  const [configRefreshResult, setConfigRefreshResult] = useState<unknown>(null)
  const [streamCheckResult, setStreamCheckResult] = useState<unknown>(null)
  const [isRefreshingConfig, setIsRefreshingConfig] = useState(false)
  const [isCheckingStreams, setIsCheckingStreams] = useState(false)

  const { data: generalHealth, isLoading: isLoadingGeneral } = useQuery({
    queryKey: ["health", "general"],
    queryFn: () => HealthService.health(),
  })

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
        key: "general",
        title: "General Health",
        data: generalHealth,
        isLoading: isLoadingGeneral,
        queryKey: ["health", "general"],
      },
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
    [
      generalHealth,
      acePoolData,
      acePoolStats,
      isLoadingGeneral,
      isLoadingAcePool,
      isLoadingAcePoolStats,
    ],
  )

  const isLoading = healthSections.some((section) => section.isLoading)

  const handleRefresh = useCallback(
    (queryKey: string[]) => {
      queryClient.invalidateQueries({ queryKey })
    },
    [queryClient],
  )

  const handleConfigRefresh = useCallback(async () => {
    setIsRefreshingConfig(true)
    try {
      const data = await ConfigService.reloadConfig()
      setConfigRefreshResult(data)
    } catch (error) {
      setConfigRefreshResult({ error: String(error) })
    } finally {
      setIsRefreshingConfig(false)
    }
  }, [])

  const handleStreamCheck = useCallback(async () => {
    setIsCheckingStreams(true)
    try {
      const data = await StreamsService.check()
      setStreamCheckResult(data)
    } catch (error) {
      setStreamCheckResult({ error: String(error) })
    } finally {
      setIsCheckingStreams(false)
    }
  }, [])

  if (isLoading) {
    return <Loading />
  }

  return (
    <VStack align="start" width="100%">
      <Box>
        <Heading size="md">Health Status</Heading>
      </Box>

      <Flex gap={4}>
        <VStack align="start" gap={2}>
          <HStack>
            <Button
              size="xs"
              onClick={handleConfigRefresh}
              loading={isRefreshingConfig}
            >
              Reload Config
            </Button>

            {configRefreshResult !== null && (
              <CodeBlock fontSize="2xs" whiteSpace="pre" flex={1}>
                {JSON.stringify(configRefreshResult, null)}
              </CodeBlock>
            )}
          </HStack>
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
            )}{" "}
          </HStack>
        </VStack>
      </Flex>

      <VStack align="start" gap={4} width="100%">
        {healthSections.map((section) => (
          <CollapsibleSection
            key={section.key}
            title={section.title}
            headerExtra={(open) =>
              open && (
                <Button
                  size="2xs"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleRefresh(section.queryKey)
                  }}
                >
                  Refresh
                </Button>
              )
            }
          >
            <CodeBlock fontSize={"2xs"} whiteSpace="pre">
              {JSON.stringify(section.data, null, 2)}
            </CodeBlock>
          </CollapsibleSection>
        ))}
      </VStack>
    </VStack>
  )
}

export default HealthManagement
