import { Container } from "@chakra-ui/react"
import { SectionSeparator } from "../ui/separator-section"
import AddScraperJson from "./Scraper/AddScraper"
import ScraperTable from "./Scraper/Table"

function ScraperManagement() {
  return (
    <Container maxW="full">
      <AddScraperJson />
      <SectionSeparator />
      <ScraperTable />
    </Container>
  )
}

export default ScraperManagement
