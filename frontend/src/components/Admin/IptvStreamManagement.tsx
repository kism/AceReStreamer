import { Container } from "@chakra-ui/react"
import IptvStreamAdminTable from "./IptvStreams/Table"

function IptvStreamManagement() {
  return (
    <Container maxW="full">
      <IptvStreamAdminTable />
    </Container>
  )
}

export default IptvStreamManagement
