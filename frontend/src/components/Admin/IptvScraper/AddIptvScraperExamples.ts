import { createListCollection } from "@chakra-ui/react"
import type { IPTVSourceApi } from "@/client"

const exampleXtream: IPTVSourceApi = {
  type: "xtream",
  name: "example-xtream",
  url: "https://example.com",
  username: "user",
  password: "pass",
  title_filter: {
    always_exclude_words: [],
    always_include_words: [],
    exclude_words: [],
    include_words: [],
    regex_postprocessing: [],
  },
  category_filter: [],
  max_active_streams: 1,
}

const exampleM3u8: IPTVSourceApi = {
  type: "m3u8",
  name: "example-m3u8",
  url: "https://example.com/playlist.m3u8",
  title_filter: {
    always_exclude_words: [],
    always_include_words: [],
    exclude_words: [],
    include_words: [],
    regex_postprocessing: [],
  },
  category_filter: [],
  max_active_streams: 1,
}

export const jsonExamples = createListCollection({
  items: [
    {
      key: "xtream",
      label: "Xtream Example",
      value: JSON.stringify(exampleXtream, null, 2),
    },
    {
      key: "m3u8",
      label: "M3U8 Example",
      value: JSON.stringify(exampleM3u8, null, 2),
    },
  ],
})
