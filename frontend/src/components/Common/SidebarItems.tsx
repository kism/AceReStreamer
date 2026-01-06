import { Box, Flex, Icon, Text } from "@chakra-ui/react"
import { useQueryClient } from "@tanstack/react-query"
import { Link as RouterLink } from "@tanstack/react-router"
import {
  FiExternalLink,
  FiLogOut,
  FiMonitor,
  FiPlay,
  FiSettings,
  FiTv,
  FiUsers,
} from "react-icons/fi"
import type { IconType } from "react-icons/lib"
import "@fontsource/fira-code/700.css"
import type { FlexProps } from "@chakra-ui/react"
import type { UserPublic } from "@/client"
import baseURL from "@/helpers"
import useAuth from "@/hooks/useAuth"

const VITE_API_URL = baseURL()

const items = [
  { icon: FiPlay, title: "Webplayer", path: "/" },
  { icon: FiMonitor, title: "Playback", path: "/info/playback" },
  { icon: FiTv, title: "IPTV", path: "/info/iptv" },
  { icon: FiSettings, title: "User Settings", path: "/settings" },
]

interface SidebarItemsProps {
  onClose?: () => void
}

interface Item {
  icon: IconType
  title: string
  path: string
}

const FlexMenuItem: React.FC<FlexProps> = ({ children, ...rest }) => {
  return (
    <Flex
      gap={4}
      px={4}
      py={2}
      _hover={{ background: "gray.subtle" }}
      alignItems="center"
      fontSize="sm"
      {...rest} // allow consumer overrides
    >
      {children}
    </Flex>
  )
}

const SidebarItems = ({ onClose }: SidebarItemsProps) => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])
  const { logout } = useAuth()

  const finalItems: Item[] = currentUser?.is_superuser
    ? [...items, { icon: FiUsers, title: "Admin", path: "/admin" }]
    : items

  const listItems = finalItems.map(({ icon, title, path }) => (
    <RouterLink key={title} to={path} onClick={onClose}>
      <FlexMenuItem>
        <Icon as={icon} alignSelf="center" />
        <Text ml={2}>{title}</Text>
      </FlexMenuItem>
    </RouterLink>
  ))

  return (
    <Box>
      {listItems}
      <FlexMenuItem
        onClick={() => window.open(`${VITE_API_URL}/docs`, "_blank")}
        cursor="pointer"
      >
        <FiExternalLink />
        <Text ml={2}>API</Text>
      </FlexMenuItem>

      <FlexMenuItem
        onClick={() => {
          logout()
        }}
        cursor="pointer"
      >
        <FiLogOut />
        <Text ml={2}>Log Out</Text>
      </FlexMenuItem>
    </Box>
  )
}

export default SidebarItems
