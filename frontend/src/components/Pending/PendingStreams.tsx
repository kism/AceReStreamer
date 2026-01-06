import { Table } from "@chakra-ui/react"
import { FiBarChart } from "react-icons/fi"
import { SkeletonText } from "../ui/skeleton"

const PendingStreams = () => (
  <Table.ScrollArea borderWidth="1px" rounded="md" height="100vh">
    <Table.Root
      size={{ base: "sm", md: "md" }}
      interactive
      stickyHeader
      tableLayout="fixed"
    >
      <Table.Header>
        <Table.Row bg="bg.subtle">
          <Table.ColumnHeader p={2} textAlign="center" width="30px">
            <FiBarChart style={{ margin: "0 auto" }} />
          </Table.ColumnHeader>
          <Table.ColumnHeader p={2} width="40%">
            Stream
          </Table.ColumnHeader>
          <Table.ColumnHeader p={2} width="auto">
            Program
          </Table.ColumnHeader>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        <Table.Row>
          <Table.Cell>
            <SkeletonText noOfLines={1} />
          </Table.Cell>
          <Table.Cell>
            <SkeletonText noOfLines={1} />
          </Table.Cell>
          <Table.Cell>
            <SkeletonText noOfLines={1} />
          </Table.Cell>
        </Table.Row>
      </Table.Body>
    </Table.Root>
  </Table.ScrollArea>
)

export default PendingStreams
