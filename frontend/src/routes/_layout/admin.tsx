import { Heading, Tabs, VStack } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import ScraperManagement from "@/components/Admin/ScraperManagement"
import UserManagement from "@/components/Admin/UserManagement"
import useAuth from "@/hooks/useAuth"

const tabsConfig = [
  { value: "users", title: "Users", component: UserManagement },
  { value: "scrapers", title: "Scrapers", component: ScraperManagement },
]

export const Route = createFileRoute("/_layout/admin")({
  component: AdminSettings,
})

function AdminSettings() {
  const { user: currentUser } = useAuth()
  const finalTabs = currentUser?.is_superuser
    ? tabsConfig.slice(0, 3)
    : tabsConfig

  if (!currentUser) {
    return null
  }

  return (
    <VStack gap={6} align="stretch">
      <Heading size="lg">Admin Settings</Heading>

      <Tabs.Root defaultValue="users" variant="subtle">
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
