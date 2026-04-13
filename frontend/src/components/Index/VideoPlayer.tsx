import { AspectRatio } from "@chakra-ui/react"

export function VideoPlayer() {
  return (
    <AspectRatio w="100%" ratio={16 / 9}>
      <div id="shaka-container" style={{ width: "100%", height: "100%" }}>
        <video style={{ width: "100%", height: "100%" }} />
      </div>
    </AspectRatio>
  )
}
