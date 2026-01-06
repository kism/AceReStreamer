import { AspectRatio } from "@chakra-ui/react"

export function VideoPlayer() {
  return (
    <AspectRatio w="100%" ratio={16 / 9}>
      <video controls />
    </AspectRatio>
  )
}
