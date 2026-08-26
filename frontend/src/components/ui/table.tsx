"use client"

import { Table } from "@chakra-ui/react"
import * as React from "react"

export type TablePreset = "outlineSm"

const presetRootProps: Record<
  TablePreset,
  Partial<React.ComponentProps<typeof Table.Root>>
> = {
  outlineSm: {
    size: "sm",
    variant: "outline",
  },
}

export interface AppTableRootProps
  extends React.ComponentProps<typeof Table.Root> {
  preset?: TablePreset
}

export const AppTableRoot = React.forwardRef<
  React.ComponentRef<typeof Table.Root>,
  AppTableRootProps
>(function AppTableRoot(props, ref) {
  const { preset, ...rest } = props
  const baseProps = preset ? presetRootProps[preset] : undefined

  return <Table.Root ref={ref} {...baseProps} {...rest} />
})

// Export the additional Table components
export const TableHeader = React.forwardRef<
  React.ComponentRef<typeof Table.Header>,
  React.ComponentProps<typeof Table.Header>
>(function TableHeader(props, ref) {
  return <Table.Header ref={ref} {...props} />
})

export const TableBody = React.forwardRef<
  React.ComponentRef<typeof Table.Body>,
  React.ComponentProps<typeof Table.Body>
>(function TableBody(props, ref) {
  return <Table.Body ref={ref} {...props} />
})

export const TableRow = React.forwardRef<
  React.ComponentRef<typeof Table.Row>,
  React.ComponentProps<typeof Table.Row>
>(function TableRow(props, ref) {
  return <Table.Row ref={ref} {...props} />
})

export const TableCell = React.forwardRef<
  React.ComponentRef<typeof Table.Cell>,
  React.ComponentProps<typeof Table.Cell>
>(function TableCell(props, ref) {
  return <Table.Cell ref={ref} px={2} py={1} {...props} />
})

export const TableColumnHeader = React.forwardRef<
  React.ComponentRef<typeof Table.ColumnHeader>,
  React.ComponentProps<typeof Table.ColumnHeader>
>(function TableColumnHeader(props, ref) {
  return (
    <Table.ColumnHeader
      textAlign={"center"}
      ref={ref}
      px={2}
      py={1}
      fontWeight={"bold"}
      {...props}
    />
  )
})
