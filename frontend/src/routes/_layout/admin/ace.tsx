import { Tabs, VStack } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import AceHealthManagement from "@/components/Admin/AceHealthManagement"
import EPGManagement from "@/components/Admin/EPGManagement"
import ScraperManagement from "@/components/Admin/ScraperManagement"
import StreamManagement from "@/components/Admin/StreamManagement"
import useAuth from "@/hooks/useAuth"
import { usePageTitle } from "@/hooks/usePageTitle"

const tabsConfig = [
  { value: "streams", title: "Streams", component: StreamManagement },
  { value: "scrapers", title: "Scrapers", component: ScraperManagement },
  { value: "epgs", title: "EPGs", component: EPGManagement },
  { value: "health", title: "Health", component: AceHealthManagement },
]

export const Route = createFileRoute("/_layout/admin/ace")({
  component: AdminAce,
})

function AdminAce() {
  usePageTitle("Admin - Ace")
  const { user: currentUser } = useAuth()

  if (!currentUser) {
    return null
  }

  return (
    <VStack gap={6} align="stretch">
      <Tabs.Root size="sm" defaultValue="streams" variant="subtle">
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
