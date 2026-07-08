import { Box, Flex, Icon, Text } from "@chakra-ui/react"
import { Link as RouterLink } from "@tanstack/react-router"
import {
  FiActivity,
  FiExternalLink,
  FiSearch,
  FiSettings,
  FiTv,
} from "react-icons/fi"
import type { IconType } from "react-icons/lib"
import "@fontsource/fira-code/700.css"
import type { FlexProps } from "@chakra-ui/react"
import baseURL from "@/helpers"

const VITE_API_URL = baseURL()

const items = [
  { icon: FiActivity, title: "Status", path: "/" },
  { icon: FiTv, title: "Channels", path: "/channels" },
  { icon: FiSearch, title: "Scrapers", path: "/scrapers" },
  { icon: FiSettings, title: "System", path: "/system" },
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
      py={2}
      px={4}
      _hover={{ background: "bg.subtle" }}
      alignItems="center"
      fontSize="sm"
      {...rest} // allow consumer overrides
    >
      {children}
    </Flex>
  )
}

const SidebarItems = ({ onClose }: SidebarItemsProps) => {
  const listItems = items.map(({ icon, title, path }: Item) => (
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
    </Box>
  )
}

export default SidebarItems
