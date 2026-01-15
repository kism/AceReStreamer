import {
  HStack,
  NativeSelectField,
  NativeSelectRoot,
  Text,
} from "@chakra-ui/react"
import type { Channel } from "./types"

interface ChannelSelectorProps {
  channels: Channel[]
  selectedChannel: string
  onChannelChange: (channelId: string) => void
}

export function ChannelSelector({
  channels,
  selectedChannel,
  onChannelChange,
}: ChannelSelectorProps) {
  return (
    <HStack>
      <Text fontWeight="bold">Channel:</Text>
      <NativeSelectRoot size="sm" width="300px">
        <NativeSelectField
          value={selectedChannel}
          onChange={(e) => onChannelChange(e.target.value)}
        >
          {channels.map((channel) => (
            <option key={channel.id} value={channel.id}>
              {channel.displayName}
            </option>
          ))}
        </NativeSelectField>
      </NativeSelectRoot>
    </HStack>
  )
}
