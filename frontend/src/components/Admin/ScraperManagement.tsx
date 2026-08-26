import { Container } from "@chakra-ui/react"
import { Button } from "../ui/button"
import { SectionSeparator } from "../ui/separator-section"
import ScraperFormDialog from "./Scraper/ScraperFormDialog"
import ScraperTable from "./Scraper/Table"

function ScraperManagement() {
  return (
    <Container maxW="full">
      <ScraperFormDialog
        trigger={
          <Button size="xs" colorPalette="teal" mt={2}>
            Add Scraper Source
          </Button>
        }
      />
      <SectionSeparator />
      <ScraperTable />
    </Container>
  )
}

export default ScraperManagement
