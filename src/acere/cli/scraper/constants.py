"""Constants for the scraper cli."""

M3U_URI_SCHEMES = {
    "infohash-main": "http://127.0.0.1:6878/ace/manifest.m3u8?infohash=",
    "content-id-main": "http://127.0.0.1:6878/ace/manifest.m3u8?content_id=",
    "content-id-ace": "acestream://",
    "content-id-horus": "plugin://script.module.horus?action=play&id=",
}
