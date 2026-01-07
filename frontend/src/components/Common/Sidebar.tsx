import { Box, Flex, Text, VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"

import "@fontsource/fira-code/700.css"

import { HealthService } from "@/client"
import useAuth from "@/hooks/useAuth"
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
                  {healthData?.version_full && (
                    <Text fontSize="xs" px={2} pb={2} color="fg.muted">
                      {healthData.version_full}
                    </Text>
                  )}
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
                    {healthData?.version_full && (
                      <Text fontSize="xs" px={2} pb={2} color="fg.muted">
                        {healthData.version_full}
                      </Text>
                    )}
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
