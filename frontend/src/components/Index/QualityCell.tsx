import { Table } from "@chakra-ui/react"

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
    <Table.Cell textAlign={"center"} fontWeight={600} color={color} {...props}>
      {quality === -1 ? "?" : quality}
    </Table.Cell>
  )
}
