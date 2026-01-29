import { Box, Collapsible, Flex, Heading, VStack } from "@chakra-ui/react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useMemo, useState } from "react"
import { FaAngleDown, FaAngleUp } from "react-icons/fa"
import { AcePoolService, EpgService, HealthService } from "@/client"
import { Button } from "@/components/ui/button"
import { CodeBlock } from "@/components/ui/code"

function HealthManagement() {
  const queryClient = useQueryClient()
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({})

  const { data: generalHealth, isLoading: isLoadingGeneral } = useQuery({
    queryKey: ["health", "general"],
    queryFn: () => HealthService.health(),
  })

  const { data: epgHealth, isLoading: isLoadingEpg } = useQuery({
    queryKey: ["health", "epg"],
    queryFn: () => EpgService.epgHealth(),
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
      {
        key: "epg",
        title: "EPG Health",
        data: epgHealth,
        isLoading: isLoadingEpg,
        queryKey: ["health", "epg"],
      },
    ],
    [
      generalHealth,
      epgHealth,
      acePoolData,
      acePoolStats,
      isLoadingGeneral,
      isLoadingEpg,
      isLoadingAcePool,
      isLoadingAcePoolStats,
    ],
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

  if (isLoading) {
    return <Box>Loading...</Box>
  }

  return (
    <VStack align="start" gap={6} width="100%">
      <Box>
        <Heading size="md">Health Status</Heading>
      </Box>

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

export default HealthManagement
