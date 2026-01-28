import { Container } from "@chakra-ui/react"
import StreamAdminTable from "./Streams/Table"

function StreamManagement() {
  return (
    <Container maxW="full">
      <StreamAdminTable />
    </Container>
  )
}

export default StreamManagement
