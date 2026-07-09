import { Heading, HStack, Text, VStack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { ConfigService } from "@/client"
import { Button } from "@/components/ui/button"
import { Loading } from "@/components/ui/loading"
import useCustomToast from "@/hooks/useCustomToast"

function ExportConfig() {
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data, isLoading } = useQuery({
    queryFn: () => ConfigService.getConfig(),
    queryKey: ["config"],
    placeholderData: (prevData) => prevData,
  })

  const handleExport = () => {
    if (!data) {
      showErrorToast("No configuration data available to export.")
      return
    }

    const configJson = JSON.stringify(data, null, 2)
    const blob = new Blob([configJson], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = `config-export-${new Date().toISOString().split("T")[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    showSuccessToast("Configuration exported successfully.")
  }

  const handleCopyToClipboard = () => {
    if (!data) {
      showErrorToast("No configuration data available to copy.")
      return
    }

    const configJson = JSON.stringify(data, null, 2)
    navigator.clipboard.writeText(configJson).then(
      () => {
        showSuccessToast("Configuration copied to clipboard.")
      },
      () => {
        showErrorToast("Failed to copy configuration to clipboard.")
      },
    )
  }

  if (isLoading) {
    return <Loading />
  }

  return (
    <VStack align="start" gap={4}>
      <Heading size="md">Export Configuration</Heading>
      <Text fontSize="sm">
        Export your current scraper configuration to a JSON file or copy it to
        the clipboard.
      </Text>

      <HStack gap={4} width="full">
        <Button
          size="xs"
          onClick={handleCopyToClipboard}
          disabled={!data}
          colorPalette="teal"
        >
          Copy to Clipboard
        </Button>
        <Button
          size="xs"
          onClick={handleExport}
          disabled={!data}
          colorPalette="teal"
        >
          Download JSON
        </Button>
      </HStack>
    </VStack>
  )
}

export default ExportConfig
