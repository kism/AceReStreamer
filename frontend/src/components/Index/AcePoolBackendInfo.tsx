import { Box, Heading, HStack, Text } from "@chakra-ui/react"
import { FiAlertTriangle } from "react-icons/fi"
import type { AcePoolForApi } from "@/client"
import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import baseURL from "@/helpers"

const VITE_API_URL = baseURL()

interface AcePoolBackendInfoProps {
  acePoolData: AcePoolForApi
  isPlaceholderData: boolean
}

export function AcePoolBackendInfo({
  acePoolData,
  isPlaceholderData,
}: AcePoolBackendInfoProps) {
  return (
    <Box>
      <Heading size="sm" py={1}>
        AceStream Backend Information
      </Heading>
      {acePoolData && acePoolData.external_url !== VITE_API_URL && (
        <Box p={2} border={"1px solid orange"} my={2}>
          <HStack>
            <Text color="fg.warning" fontSize="xl">
              <FiAlertTriangle />
            </Text>
            <Box>
              <Text color="fg.warning" fontWeight="bold">
                Backend URL ({acePoolData.external_url}) != Frontend API URL (
                {VITE_API_URL}).
              </Text>
              <Text color="fg.warning" fontWeight="bold">
                VIDEO STREAMING WILL NOT WORK
              </Text>
              <Text>
                In FastAPI, ensure that EXTERNAL_URL config option is set
                correctly.
              </Text>
              <Text>
                If you are hosting the frontend separately, ensure that
                VITE_API_URL is set correctly.
              </Text>
              <Text>
                If the frontend url in this is something weird, the frontend was
                built with that specific VITE_API_URL specified.
              </Text>
            </Box>
          </HStack>
        </Box>
      )}
      <AppTableRoot preset="outlineSm" maxW="400px">
        <TableHeader>
          <TableRow>
            <TableColumnHeader>Version</TableColumnHeader>
            <TableColumnHeader>Streams</TableColumnHeader>
            <TableColumnHeader>Transcode Audio</TableColumnHeader>
            <TableColumnHeader>Status</TableColumnHeader>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow opacity={isPlaceholderData ? 0.5 : 1}>
            <TableCell
              textAlign={"center"}
              color={
                !acePoolData.ace_version ||
                acePoolData.ace_version.version === "unknown"
                  ? "fg.error"
                  : undefined
              }
            >
              {acePoolData.ace_version?.version || "N/A"}
            </TableCell>
            <TableCell textAlign={"center"}>
              {acePoolData.ace_instances.length}/{acePoolData.max_size ?? "N/A"}
            </TableCell>
            <TableCell textAlign={"center"}>
              {acePoolData.transcode_audio ? "Yes" : "No"}
            </TableCell>
            <TableCell
              textAlign={"center"}
              color={!acePoolData.healthy ? "fg.error" : undefined}
            >
              {acePoolData.healthy ? "Healthy" : "Unhealthy"}
            </TableCell>
          </TableRow>
        </TableBody>
      </AppTableRoot>
    </Box>
  )
}
