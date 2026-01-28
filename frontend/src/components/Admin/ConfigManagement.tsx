import { Container } from "@chakra-ui/react"
import { SectionSeparator } from "../ui/separator-section"
import ExportConfig from "./Config/ExportConfig"
import ImportConfig from "./Config/ImportConfig"

function ConfigManagement() {
  return (
    <Container maxW="full">
      <ExportConfig />
      <SectionSeparator />
      <ImportConfig />
    </Container>
  )
}

export default ConfigManagement
