import { Tabs, VStack } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import ConfigManagement from "@/components/Admin/ConfigManagement"
import EPGManagement from "@/components/Admin/EPGManagement"
import HealthManagement from "@/components/Admin/HealthManagement"
import RemoteConfigManagement from "@/components/Admin/RemoteConfigManagement"
import UserManagement from "@/components/Admin/UserManagement"
import useAuth from "@/hooks/useAuth"
import { usePageTitle } from "@/hooks/usePageTitle"

const tabsConfig = [
  { value: "users", title: "Users", component: UserManagement },
  { value: "config", title: "Config", component: ConfigManagement },
  { value: "epg", title: "EPG", component: EPGManagement },
  {
    value: "remote-config",
    title: "Remote Config",
    component: RemoteConfigManagement,
  },
  { value: "health", title: "Health", component: HealthManagement },
]

export const Route = createFileRoute("/_layout/admin/general")({
  component: AdminGeneral,
})

function AdminGeneral() {
  usePageTitle("Admin - General")
  const { user: currentUser } = useAuth()

  if (!currentUser) {
    return null
  }

  return (
    <VStack gap={6} align="stretch">
      <Tabs.Root size="sm" defaultValue="users" variant="subtle">
        <Tabs.List>
          {tabsConfig.map((tab) => (
            <Tabs.Trigger key={tab.value} value={tab.value}>
              {tab.title}
            </Tabs.Trigger>
          ))}
        </Tabs.List>
        {tabsConfig.map((tab) => (
          <Tabs.Content key={tab.value} value={tab.value}>
            <tab.component />
          </Tabs.Content>
        ))}
      </Tabs.Root>
    </VStack>
  )
}
