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
import { formatDateTime, isCurrentProgram } from "./utils"

interface EPGTableProps {
  programmes: Programme[]
}

export function EPGTable({ programmes }: EPGTableProps) {
  const isMobile = useBreakpointValue({ base: true, md: false })
  const currentProgramBGColour = "teal.100"
  const currentProgramDarkBGColour = "teal.900"

  // if (isMobile) {
  if (true) {
    return (
      <VStack gap={4}>
        {programmes.map((prog, index) => {
          const isCurrent = isCurrentProgram(prog.start, prog.stop)
          return (
            <Box
              key={index}
              p={4}
              width={"100%"}
              bg={isCurrent ? currentProgramBGColour : "bg.subtle"}
              _dark={{ bg: isCurrent ? currentProgramDarkBGColour : undefined }}
            >
              <HStack justify="normal" gap={4}>
                <Text fontSize="sm" color="muted">
                  {formatDateTime(prog.start)}
                </Text>
                <Text fontWeight={"bold"}>{prog.title}</Text>
              </HStack>
              <Box mt={2} fontSize="sm" color="muted" display={ prog.description ? "block" : "none" }>
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
                _dark={{
                  bg: isCurrent ? currentProgramDarkBGColour : undefined,
                }}
                fontWeight={isCurrent ? "bold" : undefined}
              >
                <TableCell
                  textAlign={"center"}
                  whiteSpace={{ base: "normal", md: "nowrap" }}
                  width="1%"
                >
                  {formatDateTime(prog.start)}
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
