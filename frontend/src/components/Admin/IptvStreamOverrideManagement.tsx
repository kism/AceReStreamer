import { Container } from "@chakra-ui/react"
import StreamOverrides from "./IptvScraper/StreamOverrides"

function IptvStreamOverrideManagement() {
  return (
    <Container maxW="full">
      <StreamOverrides />
    </Container>
  )
}

export default IptvStreamOverrideManagement
