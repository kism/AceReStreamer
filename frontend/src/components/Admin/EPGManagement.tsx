import { Container } from "@chakra-ui/react"
import { SectionSeparator } from "../ui/separator-section"
import AddEPGJson from "./EPG/AddEPG"
import EPGTable from "./EPG/Table"

function EPGManagement() {
  return (
    <Container maxW="full">
      <AddEPGJson />
      <SectionSeparator />
      <EPGTable />
    </Container>
  )
}

export default EPGManagement
