import { Container } from "@chakra-ui/react"
import { SectionSeparator } from "../ui/separator-section"
import AddIptvScraperJson from "./IptvScraper/AddIptvScraper"
import IptvScraperTable from "./IptvScraper/Table"

function IptvScraperManagement() {
  return (
    <Container maxW="full">
      <AddIptvScraperJson />
      <SectionSeparator />
      <IptvScraperTable />
    </Container>
  )
}

export default IptvScraperManagement
