import { TableCell } from "@/components/ui/table"

export function getQualityColor(quality: number) {
  if (quality === -1) {
    return "fg.muted"
  }
  if (quality > 80) {
    return "fg.success"
  }
  if (quality >= 20) {
    return "fg.warning"
  }
  return "fg.error"
}

export function QualityCell({ quality, ...props }: { quality: number } & any) {
  const color = getQualityColor(quality)

  return (
    <TableCell textAlign={"center"} fontWeight={600} color={color} {...props}>
      {quality === -1 ? "?" : quality}
    </TableCell>
  )
}
