import { Box, Flex, Heading, IconButton } from "@chakra-ui/react"
import { FaAngleLeft, FaAngleRight, FaBars } from "react-icons/fa"

interface PageHeaderProps {
  title: string
  onMenuClick: () => void
  desktopSidebarOpen: boolean
  onDesktopSidebarToggle: () => void
}

const PageHeader = ({
  title,
  onMenuClick,
  desktopSidebarOpen,
  onDesktopSidebarToggle,
}: PageHeaderProps) => {
  return (
    <Box
      display="flex"
      bg={"bg.panel"}
      px={4}
      py={2}
      justifyContent="space-between"
    >
      <Flex alignItems="center" gap={2}>
        <IconButton
          variant="ghost"
          aria-label="Toggle Sidebar"
          onClick={onDesktopSidebarToggle}
          size="2xs"
          p="0"
          display={{ base: "none", md: "flex" }}
        >
          {desktopSidebarOpen ? <FaAngleLeft /> : <FaAngleRight />}
        </IconButton>
        <Heading size={"lg"}>{title}</Heading>
      </Flex>
      <IconButton
        variant="ghost"
        color="inherit"
        aria-label="Open Menu"
        onClick={onMenuClick}
        flexShrink={0}
        display={{ base: "flex", md: "none" }}
      >
        <FaBars />
      </IconButton>
    </Box>
  )
}

export default PageHeader
