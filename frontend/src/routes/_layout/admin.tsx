import { Tabs, VStack } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import ConfigManagement from "@/components/Admin/ConfigManagement"
import EPGManagement from "@/components/Admin/EPGManagement"
import ScraperManagement from "@/components/Admin/ScraperManagement"
import StreamManagement from "@/components/Admin/StreamManagement"
import UserManagement from "@/components/Admin/UserManagement"
import useAuth from "@/hooks/useAuth"
import { usePageTitle } from "@/hooks/usePageTitle"

const tabsConfig = [
  { value: "users", title: "Users", component: UserManagement },
  { value: "scrapers", title: "Scrapers", component: ScraperManagement },
  { value: "epgs", title: "EPGs", component: EPGManagement },
  { value: "streams", title: "Streams", component: StreamManagement },
  { value: "config", title: "Config", component: ConfigManagement },
]

export const Route = createFileRoute("/_layout/admin")({
  component: AdminSettings,
})

function AdminSettings() {
  usePageTitle("Admin Settings")
  const { user: currentUser } = useAuth()
  const finalTabs = currentUser?.is_superuser ? tabsConfig : tabsConfig

  if (!currentUser) {
    return null
  }

  return (
    <VStack gap={6} align="stretch">
      <Tabs.Root size="sm" defaultValue="users" variant="subtle">
        <Tabs.List>
          {finalTabs.map((tab) => (
            <Tabs.Trigger key={tab.value} value={tab.value}>
              {tab.title}
            </Tabs.Trigger>
          ))}
        </Tabs.List>
        {finalTabs.map((tab) => (
          <Tabs.Content key={tab.value} value={tab.value}>
            <tab.component />
          </Tabs.Content>
        ))}
      </Tabs.Root>
    </VStack>
  )
}
