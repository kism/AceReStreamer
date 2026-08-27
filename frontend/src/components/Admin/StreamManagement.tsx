import { Container } from "@chakra-ui/react"
import { SectionSeparator } from "../ui/separator-section"
import AddStream from "./Streams/AddStream"
import StreamAdminTable from "./Streams/Table"

function StreamManagement() {
  return (
    <Container maxW="950px" ml="0">
      <AddStream />
      <SectionSeparator />
      <StreamAdminTable />
    </Container>
  )
}

export default StreamManagement
