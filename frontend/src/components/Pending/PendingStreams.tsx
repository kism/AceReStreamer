import { FiBarChart } from "react-icons/fi"
import {
  AppTableRoot,
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { SkeletonText } from "../ui/skeleton"
import { AppTableScrollArea } from "../ui/table"

const PendingStreams = () => (
  <AppTableScrollArea preset="fullscreen">
    <AppTableRoot preset="interactiveSticky">
      <TableHeader>
        {/* Due to sticky header we set bg.subtle */}
        <TableRow bg="bg.subtle">
          <TableColumnHeader width="30px">
            <FiBarChart style={{ margin: "0 auto" }} />
          </TableColumnHeader>
          <TableColumnHeader width="90%">Stream</TableColumnHeader>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>
            <SkeletonText noOfLines={1} />
          </TableCell>
          <TableCell>
            <SkeletonText noOfLines={1} />
          </TableCell>
        </TableRow>
      </TableBody>
    </AppTableRoot>
  </AppTableScrollArea>
)

export default PendingStreams
