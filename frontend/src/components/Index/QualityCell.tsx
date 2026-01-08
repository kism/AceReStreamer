import { TableCell } from "@/components/ui/table"
import { QUALITY_COLORS } from "./constants"

export function QualityCell({ quality, ...props }: { quality: number } & any) {
  let color = "black"
  if (quality === -1) {
    color = QUALITY_COLORS.unknown
  } else if (quality > 80) {
    color = QUALITY_COLORS.good
  } else if (quality >= 20) {
    color = QUALITY_COLORS.medium
  } else {
    color = QUALITY_COLORS.poor
  }

  return (
    <TableCell textAlign={"center"} fontWeight={600} color={color} {...props}>
      {quality === -1 ? "?" : quality}
    </TableCell>
  )
}
