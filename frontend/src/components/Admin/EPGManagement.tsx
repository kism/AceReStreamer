import { Container } from "@chakra-ui/react"
import AddEPGJson from "./EPG/AddEPG"
import EPGTable from "./EPG/Table"

function EPGManagement() {
  return (
    <Container maxW="full">
      <AddEPGJson />
      <EPGTable />
    </Container>
  )
}

export default EPGManagement
