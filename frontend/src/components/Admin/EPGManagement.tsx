import { Container } from "@chakra-ui/react"
import { SectionSeparator } from "../ui/separator-section"
import AddEPGJson from "./EPG/AddEPG"
import EPGTable from "./EPG/Table"
import XcEpgSourcesTable from "./EPG/XcEpgSourcesTable"

function EPGManagement() {
  return (
    <Container maxW="full">
      <AddEPGJson />
      <SectionSeparator />
      <EPGTable />
      <SectionSeparator />
      <XcEpgSourcesTable />
    </Container>
  )
}

export default EPGManagement
