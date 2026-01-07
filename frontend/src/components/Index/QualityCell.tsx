import { TableCell } from "@/components/ui/table"

export function QualityCell({ quality, ...props }: { quality: number } & any) {
  let color = "black"
  if (quality === -1) {
    color = "gray"
  } else if (quality > 80) {
    color = "green.500"
  } else if (quality >= 20) {
    color = "yellow.500"
  } else {
    color = "red.500"
  }

  return (
    <TableCell textAlign={"center"} fontWeight={600} color={color} {...props}>
      {quality === -1 ? "?" : quality}
    </TableCell>
  )
}
