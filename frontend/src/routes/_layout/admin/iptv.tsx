import { Tabs, VStack } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import IptvScraperManagement from "@/components/Admin/IptvScraperManagement"
import IptvStreamManagement from "@/components/Admin/IptvStreamManagement"
import IptvStreamOverrideManagement from "@/components/Admin/IptvStreamOverrideManagement"
import useAuth from "@/hooks/useAuth"
import { usePageTitle } from "@/hooks/usePageTitle"

const tabsConfig = [
  { value: "streams", title: "Streams", component: IptvStreamManagement },
  { value: "scrapers", title: "Scrapers", component: IptvScraperManagement },
  {
    value: "overrides",
    title: "Stream Overrides",
    component: IptvStreamOverrideManagement,
  },
]

export const Route = createFileRoute("/_layout/admin/iptv")({
  component: AdminIptv,
})

function AdminIptv() {
  usePageTitle("Admin - IPTV")
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
