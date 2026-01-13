import { createListCollection } from "@chakra-ui/react"
import type { AceScraperSourceApi } from "@/client"

const exampleIPTV: AceScraperSourceApi = {
  type: "iptv",
  name: "example-scraper",
  url: "https://example.com/playlist.m3u",
  title_filter: {
    always_exclude_words: [],
    always_include_words: [],
    exclude_words: [],
    include_words: [],
    regex_postprocessing: [],
  },
}

const exampleAPI: AceScraperSourceApi = {
  type: "api",
  name: "example-scraper",
  url: "https://api.example.com/list?api_key=test_api_key",
  title_filter: {
    always_exclude_words: [],
    always_include_words: [],
    exclude_words: [],
    include_words: [],
    regex_postprocessing: [],
  },
}

const exampleHTML: AceScraperSourceApi = {
  type: "html",
  name: "example-scraper",
  url: "https://example.com",
  title_filter: {
    always_exclude_words: [],
    always_include_words: [],
    exclude_words: [],
    include_words: [],
    regex_postprocessing: [],
  },
  html_filter: {
    target_class: "",
    check_sibling: false,
  },
}

export const jsonExamples = createListCollection({
  items: [
    {
      key: "iptv",
      label: "IPTV Example",
      value: JSON.stringify(exampleIPTV, null, 2),
    },
    {
      key: "api",
      label: "API Example",
      value: JSON.stringify(exampleAPI, null, 2),
    },
    {
      key: "html",
      label: "HTML Example",
      value: JSON.stringify(exampleHTML, null, 2),
    },
  ],
})
