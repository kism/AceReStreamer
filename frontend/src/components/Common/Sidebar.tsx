import { Box, Flex, Text, VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"

import "@fontsource/fira-code/700.css"

import { type HealthHealthResponse, HealthService } from "@/client"
import useAuth from "@/hooks/useAuth"
import packageJson from "../../../package.json"
import {
  DrawerBackdrop,
  DrawerBody,
  DrawerCloseTrigger,
  DrawerContent,
  DrawerRoot,
} from "../ui/drawer"
import SidebarItems from "./SidebarItems"

interface SidebarProps {
  mobileOpen: boolean
  onMobileOpenChange: (open: boolean) => void
  desktopOpen: boolean
}

const AceReStreamerLogo = () => (
  <Text fontSize="2xl" fontWeight="700" fontFamily="'Fira Code', monospace">
    AceReStreamer
  </Text>
)

interface VersionBlockProps {
  healthData: HealthHealthResponse | null
}

function VersionBlock({ healthData }: VersionBlockProps) {
  const textProps = {
    fontSize: "xs",
    p: 2,
    truncate: true,
    maxW: "sm",
    color: "fg.muted",
  }

  const backendVersion = healthData?.version ?? "unknown"
  const backendVersionFull = healthData?.version_full ?? "unknown"

  const frontendVersionFull = `${packageJson.version}-${__GIT_BRANCH__}/${__GIT_COMMIT__}`
  const frontendVersion = packageJson.version

  if (
    //If we have full version information from both and they match
    backendVersionFull === frontendVersionFull ||
    //If the short versions match, and there is no git info from the backend
    (backendVersion === frontendVersion &&
      backendVersion === backendVersionFull)
  ) {
    return <Text {...textProps}>{backendVersionFull}</Text>
  }

  return (
    <Box>
      <Text {...textProps}>
        {frontendVersionFull}
        <br />
        {backendVersionFull}
      </Text>
    </Box>
  )
}

const Sidebar = ({
  mobileOpen,
  onMobileOpenChange,
  desktopOpen,
}: SidebarProps) => {
  const { user: currentUser } = useAuth()
  const { data: healthData } = useQuery({
    queryKey: ["health"],
    queryFn: HealthService.health,
  })

  return (
    <>
      {/* Mobile */}
      <DrawerRoot
        placement="start"
        open={mobileOpen}
        onOpenChange={(e) => onMobileOpenChange(e.open)}
      >
        <DrawerBackdrop />
        <DrawerContent bg="bg.emphasized" maxW="270px">
          <DrawerCloseTrigger />
          <DrawerBody>
            <Flex flexDir="column" justify="space-between" h="full">
              <Box>
                <VStack py={2} gap={2} align="stretch">
                  <AceReStreamerLogo />
                  <SidebarItems onClose={() => onMobileOpenChange(false)} />
                </VStack>
              </Box>
              {currentUser?.username && (
                <Box>
                  <Text fontSize="sm" p={2} truncate maxW="sm">
                    Logged in as: {currentUser.username}
                  </Text>
                  <VersionBlock healthData={healthData ?? null} />
                </Box>
              )}
            </Flex>
          </DrawerBody>
          <DrawerCloseTrigger />
        </DrawerContent>
      </DrawerRoot>

      {/* Desktop */}

      <Box
        display={{ base: "none", md: "flex" }}
        position="relative"
        bg="bg.emphasized"
        w="auto"
        px={desktopOpen ? 2 : 0}
        h="100vh"
        transition="width 0.3s ease"
        overflow="hidden"
      >
        <Flex direction="column" w="full" h="full">
          <Flex
            align="center"
            gap={2}
            p={2}
            pt={2}
            display={desktopOpen ? "flex" : "none"}
          >
            <AceReStreamerLogo />
          </Flex>

          {desktopOpen && (
            <Box flex="1" p={2} pt={0}>
              <Flex flexDir="column" justify="space-between" h="full">
                <Box>
                  <SidebarItems />
                </Box>
                {currentUser?.username && (
                  <Box>
                    <Text fontSize="sm" p={2} truncate maxW="sm">
                      Logged in as: {currentUser.username}
                    </Text>
                    <VersionBlock healthData={healthData ?? null} />
                  </Box>
                )}
              </Flex>
            </Box>
          )}
        </Flex>
      </Box>
    </>
  )
}

export default Sidebar
