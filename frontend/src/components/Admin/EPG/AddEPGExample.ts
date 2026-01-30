import type { EPGInstanceConf_Input } from "@/client"

export const exampleEPGSource: EPGInstanceConf_Input = {
  format: "xml.gz",
  url: "https://example.com/epg.xml.gz",
  tvg_id_overrides: {},
}
