import { Box, HStack, Text, useBreakpointValue, VStack } from "@chakra-ui/react"
import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { Programme } from "./types"
import { isCurrentProgram, parseXmltvDate } from "./utils"

interface EPGTableProps {
  programmes: Programme[]
}

function formatDateTime(dateTimeStr: string): [string, string] {
  if (!dateTimeStr) return ["", ""]
  // XMLEPG format: YYYYMMDDHHmmss +0000

  const date = parseXmltvDate(dateTimeStr)

  const dateLine = date.toLocaleDateString([], {
    day: "numeric",
    month: "short",
  })
  const timeLine = date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  })

  return [dateLine, timeLine]
}

function DateTimeHStack({ dateTimeStr }: { dateTimeStr: string }) {
  const [dateLine, timeLine] = formatDateTime(dateTimeStr)
  return (
    <HStack justify="center" gap={2} whiteSpace="nowrap">
      <Text>{dateLine}</Text>
      <Text>{timeLine}</Text>
    </HStack>
  )
}

function DateTimeVStack({
  dateTimeStr,
  fontWeight,
}: {
  dateTimeStr: string
  fontWeight?: string
}) {
  const [dateLine, timeLine] = formatDateTime(dateTimeStr)
  return (
    <VStack alignItems="flex-start" gap={0} whiteSpace="nowrap">
      <Text fontWeight={fontWeight}>{dateLine}</Text>
      <Text fontWeight={fontWeight}>{timeLine}</Text>
    </VStack>
  )
}

export function EPGTable({ programmes }: EPGTableProps) {
  const isMobile = useBreakpointValue({ base: true, md: false })
  const isLargeScreen = useBreakpointValue({ base: false, lg: true })
  const currentProgramBGColour = "teal.900"

  if (isMobile) {
    return (
      <VStack gap={2}>
        {programmes.map((prog, index) => {
          const isCurrent = isCurrentProgram(prog.start, prog.stop)
          return (
            <Box
              key={index}
              p={2}
              width={"100%"}
              bg={isCurrent ? currentProgramBGColour : "bg.subtle"}
            >
              <HStack justify="normal" gap={4}>
                <DateTimeVStack
                  fontWeight={isCurrent ? "bold" : "normal"}
                  dateTimeStr={prog.start}
                />
                <Text fontWeight={isCurrent ? "bold" : "normal"}>
                  {prog.title}
                </Text>
              </HStack>
              <Box
                mt={2}
                fontSize="sm"
                color="muted"
                display={prog.description ? "block" : "none"}
              >
                {prog.description}
              </Box>
            </Box>
          )
        })}
      </VStack>
    )
  }

  return (
    <AppTableRoot preset="outlineSm">
      <TableHeader zIndex={1}>
        <TableRow bg="bg.subtle">
          <TableColumnHeader>Start</TableColumnHeader>
          <TableColumnHeader>Title</TableColumnHeader>
          <TableColumnHeader>Description</TableColumnHeader>
        </TableRow>
      </TableHeader>
      <TableBody>
        {programmes.length === 0 ? (
          <TableRow>
            <TableCell colSpan={4} textAlign="center">
              No programmes found for this channel
            </TableCell>
          </TableRow>
        ) : (
          programmes.map((prog, index) => {
            const isCurrent = isCurrentProgram(prog.start, prog.stop)
            return (
              <TableRow
                key={index}
                bg={isCurrent ? currentProgramBGColour : undefined}
                fontWeight={isCurrent ? "bold" : undefined}
              >
                <TableCell width="1%">
                  {isLargeScreen ? (
                    <DateTimeHStack dateTimeStr={prog.start} />
                  ) : (
                    <DateTimeVStack dateTimeStr={prog.start} />
                  )}
                </TableCell>

                <TableCell
                  width={{ base: "100px", md: "200px", lg: "250px" }}
                  maxW="300px"
                  whiteSpace="wrap"
                  title={prog.title}
                >
                  {prog.title}
                </TableCell>
                <TableCell maxW="0" whiteSpace="wrap" title={prog.description}>
                  {prog.description}
                </TableCell>
              </TableRow>
            )
          })
        )}
      </TableBody>
    </AppTableRoot>
  )
}
