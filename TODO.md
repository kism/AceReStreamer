# TODO

- ~~old stream culling~~
- ~~cookie duration~~
- ace api should include hls url, including token, why not
- separate ace settings menu in frontend
- streaming response for hls
- no multiple gets for token in webui
- check for typing.Any
- mpegts proxy?
- proxy XC/m3u8 feature
  - change how xc id is mapped
    - ace stream and proxied hls stream are different
  - config
    - xc
      - username
      - password
      - url
    - m3u8
      - url
  - filtering
    - by name, or group
  - epg
    - Fetch from XC
    - Kinda fuzzy matching
  - pooling,
    - Each playlist should have an optional maximum number of streams active
  - cache, redis?
  - /hls/web/<whatever>
  - xc scraper
  - m3u8 scraper that is shared with ace

Hello, right now this program scrapes and proxies ace stream, the next step is proxying IPTV (m3u8, xtream).

The endpoint non-ace for hls streams will be /hls/web/<whatever>?token=<token>, and for segments it will be /hls/web-segment/<whatever>/<segment>, the segment url will need to be generated from the upstream playlist and be able to map. No token for segments so that nginx can cache them. There should be no caching backported to ACE since ace handles its own caching.

In the config for IPTV sources, there should be two sections, one for xtream and one for m3u8. The xtream section should have username, password, and url, and the m3u8 section should have url. Each of the playlists sould create a list of candidate streams when processed with category, stream title, tvg-id, tvg-logo.

There is logic for m3u8 scraping that already exists in the ace scraper, this should be refactored to be shared between both the ace and m3u8 scrapers. The xtream scraper will be separate since it needs to handle authentication and parsing the playlist from the api response. There are already Pydantic models for the xtream api response, so that should be used to parse the response and create the list of candidate streams.

In each of the playlist config definitions

- The user should be able to filter by title or category. Scraped playlists (both iptv and xc) should be cached for an hour.
- The user should be able to specify a maximum number of active streams for each playlist. If the maximum is greater than what the XC player_api.json specifies there should be a warning in the logs.

Don't worry about the EPG for now, this will need to be fixed later.

Before you get started, how much benefit would there be to cache in Redis? Right now this is all handled on disk in the instance/ directory. I don't want high ram usage and i'm proxying HLS segments, plus xml EPGs get pretty big too. Is there other options?

---

The RemoteSettingsFetcher should not include the iptv proxy settings

The created adhoc stream list from ace in scraper should have all the x-last-found= fields filled in, can you check that that's still the case? Is this tested?
