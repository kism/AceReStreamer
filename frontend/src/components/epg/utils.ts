import type { EPGData } from "./types"

export function parseEPGXML(xmlText: string): EPGData {
  try {
    const parser = new DOMParser()
    const xmlDoc = parser.parseFromString(xmlText, "text/xml")

    // Check for parsing errors
    const parserError = xmlDoc.querySelector("parsererror")
    if (parserError) {
      console.error("XML parsing error:", parserError.textContent)
      throw new Error("Failed to parse EPG XML")
    }

    const channels: EPGData["channels"] = []
    const programmes: EPGData["programmes"] = []

    // Parse channels
    const channelElements = xmlDoc.getElementsByTagName("channel")
    console.log("Found channels:", channelElements.length)
    for (let i = 0; i < channelElements.length; i++) {
      const chan = channelElements[i]
      const id = chan.getAttribute("id") || ""
      const displayNameElement = chan.getElementsByTagName("display-name")[0]
      const displayName = displayNameElement?.textContent || id

      channels.push({ id, displayName })
    }

    // Parse programmes
    const programmeElements = xmlDoc.getElementsByTagName("programme")
    console.log("Found programmes:", programmeElements.length)
    for (let i = 0; i < programmeElements.length; i++) {
      const prog = programmeElements[i]
      const channel = prog.getAttribute("channel") || ""
      const start = prog.getAttribute("start") || ""
      const stop = prog.getAttribute("stop") || ""

      const titleElement = prog.getElementsByTagName("title")[0]
      const title = titleElement?.textContent || ""

      const descElement = prog.getElementsByTagName("desc")[0]
      const description = descElement?.textContent || ""

      programmes.push({ channel, start, stop, title, description })
    }

    return { channels, programmes }
  } catch (err) {
    console.error("Error in parseEPGXML:", err)
    throw err
  }
}

export function formatDateTime(dateTimeStr: string): string {
  if (!dateTimeStr) return ""
  // Format: YYYYMMDDHHmmss +0000
  const dayNum = Number.parseInt(dateTimeStr.substring(6, 8), 10)
  const hour = dateTimeStr.substring(8, 10)
  const minute = dateTimeStr.substring(10, 12)

  const getOrdinalSuffix = (day: number): string => {
    if (day > 3 && day < 21) return "th"
    switch (day % 10) {
      case 1:
        return "st"
      case 2:
        return "nd"
      case 3:
        return "rd"
      default:
        return "th"
    }
  }

  return `${dayNum}${getOrdinalSuffix(dayNum)} ${hour}:${minute}`
}

export function isCurrentProgram(startStr: string, stopStr: string): boolean {
  if (!startStr || !stopStr) return false

  // Parse XMLTV format: YYYYMMDDHHmmss +0000
  const parseXmltvTime = (timeStr: string): Date => {
    const year = Number.parseInt(timeStr.substring(0, 4), 10)
    const month = Number.parseInt(timeStr.substring(4, 6), 10) - 1 // JS months are 0-indexed
    const day = Number.parseInt(timeStr.substring(6, 8), 10)
    const hour = Number.parseInt(timeStr.substring(8, 10), 10)
    const minute = Number.parseInt(timeStr.substring(10, 12), 10)
    const second = Number.parseInt(timeStr.substring(12, 14), 10)
    return new Date(year, month, day, hour, minute, second)
  }

  const now = new Date()
  const start = parseXmltvTime(startStr)
  const stop = parseXmltvTime(stopStr)

  return now >= start && now <= stop
}
