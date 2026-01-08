import { Flex } from "@chakra-ui/react"
import { createFileRoute, Outlet, redirect } from "@tanstack/react-router"
import { useState } from "react"
import PageHeader from "@/components/Common/Header"
import Sidebar from "@/components/Common/Sidebar"
import { isLoggedIn } from "@/hooks/useAuth"
import { PageTitleContext, usePageTitleState } from "@/hooks/usePageTitle"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
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
          <Flex flex="1" direction="column" px={4} py={2} overflowY="auto">
            <Outlet />
          </Flex>
        </Flex>
      </Flex>
    </PageTitleContext.Provider>
  )
}
export default Layout
