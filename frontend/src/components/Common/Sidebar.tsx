import { Box, Flex, IconButton, Link, Text } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { FaAngleLeft, FaAngleRight, FaBars } from "react-icons/fa"
import "@fontsource/fira-code/700.css"

import { HealthService } from "@/client"
import useAuth from "@/hooks/useAuth"
import {
  DrawerBackdrop,
  DrawerBody,
  DrawerCloseTrigger,
  DrawerContent,
  DrawerRoot,
  DrawerTrigger,
} from "../ui/drawer"
import SidebarItems from "./SidebarItems"

const Sidebar = () => {
  const { user: currentUser } = useAuth()
  const { data: healthData } = useQuery({
    queryKey: ["health"],
    queryFn: HealthService.health,
  })
  const [open, setOpen] = useState(false)
  const [desktopOpen, setDesktopOpen] = useState(true)

  return (
    <>
      {/* Mobile */}
      <DrawerRoot
        placement="start"
        open={open}
        onOpenChange={(e) => setOpen(e.open)}
      >
        <DrawerBackdrop />
        <DrawerTrigger asChild>
          <IconButton
            variant="ghost"
            color="inherit"
            display={{ base: "flex", md: "none" }}
            aria-label="Open Menu"
            position="absolute"
            zIndex="100"
            m={4}
          >
            <FaBars />
          </IconButton>
        </DrawerTrigger>
        <DrawerContent maxW="xs">
          <DrawerCloseTrigger />
          <DrawerBody>
            <Flex flexDir="column" justify="space-between">
              <Box>
                <SidebarItems onClose={() => setOpen(false)} />
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
        pr={desktopOpen ? 5 : 0}
        h="100vh"
        transition="width 0.3s ease"
        overflow="hidden"
      >
        <Flex direction="column" w="full" h="full">
          <Flex
            align="center"
            gap={desktopOpen ? 2 : 0}
            p={desktopOpen ? 2 : 1}
            pt={desktopOpen ? 2 : 3}
          >
            <IconButton
              variant="ghost"
              color="inherit"
              aria-label="Toggle Menu"
              onClick={() => setDesktopOpen(!desktopOpen)}
              size={desktopOpen ? "sm" : "xs"}
            >
              {desktopOpen ? <FaAngleLeft /> : <FaAngleRight />}
            </IconButton>

            <Link href="/" display={desktopOpen ? "block" : "none"}>
              <Text
                fontSize="2xl"
                fontWeight="700"
                fontFamily="'Fira Code', monospace"
              >
                AceReStreamer
              </Text>
            </Link>
          </Flex>

          {desktopOpen && (
            <Box flex="1" p={4} pt={0}>
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
