export interface Channel {
  id: string
  displayName: string
}

export interface Programme {
  channel: string
  start: string
  stop: string
  title: string
  description: string
}

export interface EPGData {
  channels: Channel[]
  programmes: Programme[]
}
