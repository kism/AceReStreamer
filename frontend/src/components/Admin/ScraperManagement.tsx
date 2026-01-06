import { Container } from "@chakra-ui/react"
import AddScraperJson from "./Scraper/AddScraper"
import ScraperTable from "./Scraper/Table"

function ScraperManagement() {
  return (
    <Container maxW="full">
      <AddScraperJson />
      <ScraperTable />
    </Container>
  )
}

export default ScraperManagement
