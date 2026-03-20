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
  - cache m3u8 fetches for iptv proxy?

## Fix

This logic might be cooked

```python
    iptv_manager = get_iptv_proxy_manager()
    segment_url = iptv_manager.get_segment_upstream_url(slug, segment)
```

Use the name filter for categories too.
