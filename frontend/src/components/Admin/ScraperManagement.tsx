import { Container } from "@chakra-ui/react"
import { SectionSeparator } from "../ui/separator-section"
import AddScraperJson from "./Scraper/AddScraper"
import NameOverrides from "./Scraper/NameOverrides"
import ScraperTable from "./Scraper/Table"

function ScraperManagement() {
  return (
    <Container maxW="full">
      <AddScraperJson />
      <SectionSeparator />
      <ScraperTable />
      <SectionSeparator />
      <NameOverrides />
    </Container>
  )
}

export default ScraperManagement
