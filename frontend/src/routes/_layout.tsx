import { Flex } from "@chakra-ui/react"
import { createFileRoute, Outlet } from "@tanstack/react-router"
import { useState } from "react"
import PageHeader from "@/components/Common/Header"
import Sidebar from "@/components/Common/Sidebar"
import { PageTitleContext, usePageTitleState } from "@/hooks/usePageTitle"

export const Route = createFileRoute("/_layout")({
  component: Layout,
})

function Layout() {
  const { title, setTitle } = usePageTitleState()
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false)
  const [desktopSidebarOpen, setDesktopSidebarOpen] = useState(true)

  return (
    <PageTitleContext.Provider value={{ title, setTitle }}>
      <Flex h="100vh" overflow="hidden">
        <Sidebar
          mobileOpen={mobileDrawerOpen}
          onMobileOpenChange={setMobileDrawerOpen}
          desktopOpen={desktopSidebarOpen}
        />
        <Flex flex="1" direction="column" overflow="hidden">
          <PageHeader
            title={title}
            onMenuClick={() => setMobileDrawerOpen(true)}
            desktopSidebarOpen={desktopSidebarOpen}
            onDesktopSidebarToggle={() =>
              setDesktopSidebarOpen(!desktopSidebarOpen)
            }
          />
          <Flex
            flex="1"
            direction="column"
            px={{ base: 1, sm: 4 }}
            py={2}
            overflowY="auto"
          >
            <Outlet />
          </Flex>
        </Flex>
      </Flex>
    </PageTitleContext.Provider>
  )
}
export default Layout
