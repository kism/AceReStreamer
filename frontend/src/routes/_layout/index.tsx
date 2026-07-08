import { Box } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { AcePoolSection } from "@/components/Index/AcePoolSection"
import { StreamTable } from "@/components/Index/StreamTable"
import { usePageTitle } from "@/hooks/usePageTitle"

export const Route = createFileRoute("/_layout/")({
  component: Streams,
})

function Streams() {
  usePageTitle("Streams")

  return (
    <Box maxW="800px">
      <AcePoolSection />
      <StreamTable />
    </Box>
  )
}
