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
  return (
    <AppTableRoot preset="outlineSm">
      <TableHeader zIndex={1}>
        <TableRow bg="bg.subtle">
          <TableColumnHeader whiteSpace="nowrap">Start</TableColumnHeader>
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
                bg={isCurrent ? "teal.100" : undefined}
                _dark={{ bg: isCurrent ? "teal.900" : undefined }}
                fontWeight={isCurrent ? "bold" : undefined}
              >
                <TableCell textAlign={"center"} whiteSpace="nowrap" width="1%">
                  {formatDateTime(prog.start)}
                </TableCell>

                <TableCell whiteSpace="nowrap" width="1%">
                  {prog.title}
                </TableCell>
                <TableCell
                  overflow="hidden"
                  maxW="0"
                  whiteSpace="nowrap"
                  textOverflow="ellipsis"
                  title={prog.description}
                >
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
