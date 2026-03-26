# TODO

- mpegts proxy?
- ~~old stream culling~~
- check for typing.Any
- ~~Cache m3u8 fetches for iptv proxy~~
- /hls/web/<whatever> fix in frontend
- add HEAD method to /hls/ace and /hls/web
- shaka player
  - fix lazy loading
- more settings for settings import
  - toggle EPG or Ace scraper
  - epg config import doesnt affect other epgs (with different URLs)
- frontend
  - `module.loadPlayStream(`/hls/ace/${data?.content_id}`)` rename
  - `video.addEventListener("contextmenu", (e) => {` does nothing?
  - remover Player: Playing from the table
  - put video source stats instead
