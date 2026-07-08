import { createFileRoute } from "@tanstack/react-router"
import ScraperManagement from "@/components/Admin/ScraperManagement"
import { usePageTitle } from "@/hooks/usePageTitle"

export const Route = createFileRoute("/_layout/scrapers")({
  component: Scrapers,
})

function Scrapers() {
  usePageTitle("Scrapers")

  return <ScraperManagement />
}
