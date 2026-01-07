import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { SkeletonText } from "../ui/skeleton"

const PendingUsers = () => (
  <AppTableRoot preset="outlineSm">
    <TableHeader>
      <TableRow>
        <TableColumnHeader w="sm">Full name</TableColumnHeader>
        <TableColumnHeader w="sm">Email</TableColumnHeader>
        <TableColumnHeader w="sm">Role</TableColumnHeader>
        <TableColumnHeader w="sm">Status</TableColumnHeader>
        <TableColumnHeader w="sm">Actions</TableColumnHeader>
      </TableRow>
    </TableHeader>
    <TableBody>
      {[...Array(5)].map((_, index) => (
        <TableRow key={index}>
          <TableCell>
            <SkeletonText noOfLines={1} />
          </TableCell>
          <TableCell>
            <SkeletonText noOfLines={1} />
          </TableCell>
          <TableCell>
            <SkeletonText noOfLines={1} />
          </TableCell>
          <TableCell>
            <SkeletonText noOfLines={1} />
          </TableCell>
          <TableCell>
            <SkeletonText noOfLines={1} />
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  </AppTableRoot>
)

export default PendingUsers
