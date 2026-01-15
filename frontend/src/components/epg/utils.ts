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
    for (let i = 0; i < channelElements.length; i++) {
      const chan = channelElements[i]
      const id = chan.getAttribute("id") || ""
      const displayNameElement = chan.getElementsByTagName("display-name")[0]
      const displayName = displayNameElement?.textContent || id

      channels.push({ id, displayName })
    }

    // Parse programmes
    const programmeElements = xmlDoc.getElementsByTagName("programme")
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
  // XMLEPG format: YYYYMMDDHHmmss +0000
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

export function parseXmltvDate(xmltvDate: string): Date {
  // Trim and split timezone
  const [datePart, tzPart] = xmltvDate.trim().split(" ")

  const year = datePart.slice(0, 4)
  const month = datePart.slice(4, 6)
  const day = datePart.slice(6, 8)
  const hour = datePart.slice(8, 10)
  const minute = datePart.slice(10, 12)
  const second = datePart.slice(12, 14)

  // Convert +0800 → +08:00
  const tz = tzPart ? `${tzPart.slice(0, 3)}:${tzPart.slice(3)}` : "Z"

  return new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}${tz}`)
}

export function isCurrentProgram(startStr: string, stopStr: string): boolean {
  if (!startStr || !stopStr) return false

  const now = new Date()
  const start = parseXmltvDate(startStr)
  const stop = parseXmltvDate(stopStr)

  return now >= start && now <= stop
}
