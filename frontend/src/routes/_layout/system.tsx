import { Tabs, VStack } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import ConfigManagement from "@/components/Admin/ConfigManagement"
import HealthManagement from "@/components/Admin/HealthManagement"
import RemoteConfigManagement from "@/components/Admin/RemoteConfigManagement"
import { usePageTitle } from "@/hooks/usePageTitle"

const tabsConfig = [
  { value: "config", title: "Config", component: ConfigManagement },
  {
    value: "remote-config",
    title: "Remote Config",
    component: RemoteConfigManagement,
  },
  { value: "health", title: "Health", component: HealthManagement },
]

export const Route = createFileRoute("/_layout/system")({
  component: SystemSettings,
})

function SystemSettings() {
  usePageTitle("System")

  return (
    <VStack gap={6} align="stretch">
      <Tabs.Root size="sm" defaultValue="config" variant="subtle">
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
