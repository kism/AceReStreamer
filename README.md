# acerestreamer

[![Check](https://github.com/kism/AceReStreamer/actions/workflows/check.yml/badge.svg)](https://github.com/kism/AceReStreamer/actions/workflows/check.yml)
[![CheckType](https://github.com/kism/AceReStreamer/actions/workflows/check_types.yml/badge.svg)](https://github.com/kism/AceReStreamer/actions/workflows/check_types.yml)
[![Test](https://github.com/kism/AceReStreamer/actions/workflows/test.yml/badge.svg)](https://github.com/kism/AceReStreamer/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kism/AceReStreamer/graph/badge.svg?token=FPGDA0ODT7)](https://codecov.io/gh/kism/AceReStreamer)

## Prerequisites

Install uv <https://docs.astral.sh/uv/getting-started/installation/>

## Run

### Prerequsites

Run ace stream, I use docker

```bash
docker run -t -p 127.0.0.1:6878:6878 ghcr.io/martinbjeldbak/acestream-http-proxy
# Or if you are in a situation without UPnP, you will need to port forward 8621
docker run -t -p 127.0.0.1:6878:6878 -p 8621:8621 ghcr.io/martinbjeldbak/acestream-http-proxy
```

Or even better, use docker compose

```bash
docker compose up -d
```

### Get node_modules

```bash
nvm use 24
npm install
```

### Run Dev

```bash
uv venv
source .venv/bin/activate
uv sync
flask --app acerestreamer run --port 5100
```

### Run Prod

```bash
uv venv
source .venv/bin/activate
uv sync --no-group test --no-group type --no-group lint

.venv/bin/waitress-serve \
    --listen "127.0.0.1:5100" \
    --trusted-proxy '*' \
    --trusted-proxy-headers 'x-forwarded-for x-forwarded-proto x-forwarded-port' \
    --log-untrusted-proxy-headers \
    --clear-untrusted-proxy-headers \
    --threads 4 \
    --call acerestreamer:create_app
```

## todo

### Features

- /health endpoint
- pytest
- vitest?
- iptv api
  - ~~more on the iptv guide~~
  - per source iptv feeds
- bootstrap on first launch
  - administrative account
  - ~~json for the config file~~
- determine stream health from m3u8

### Apps that don't work

see iptv.html.j2

### Done

- ~~publish~~
  - ~~streams/flat~~
  - ~~streams/by_source~~
- ~~breadcrumb~~
- ~~less recursion in patient search i think~~
- ~~scraper list~~
  - ~~populate quality~~
  - ~~cache the quality~~
- ~~figure out types for get_streams and get_streams_flat~~
  - ~~pydantic to replace typedict?~~
- ~~actually set stream id in js~~
- ~~use unauthorised for endpoints that require auth~~
- ~~player stopped by default~~
- ~~add about page~~
- ~~add table sorting~~
- ~~iptv support~~
- ~~instructions page~~
- ~~scraper global settings~~
  - ~~frequency~~
  - ~~forbidden titles~~
- ~~investigate if I need to reload nginx~~
- ~~get media info from hls.js~~ impossible
- ~~investigate .copy()~~
- ~~login page~~
- ~~document iptv clients~~
- ~~resize video player on page load, maybe mobile only~~
- ~~api playground~~
- ~~caching for pages~~
- ~~biome~~
- ~~cache the sources~~
- ~~reload player on failure a couple of times~~
- ~~keep locked in streams alive~~
- ~~pools api~~
- ~~ace_pool more verbose api~~
- ~~ace_pool on info on /stream~~
- ~~health check the ace pool~~
- ~~chromecast / airplay support~~ abandoned chromecast, airplay might work
- ~~ace pool keep alive status~~
- ~~group the fetchers~~
- ~~actually fetch from sites in a thread~~
- ~~api reference~~
- ~~get content_id from ace/manifest.m3u8 yeah? It redirects~~
- ~~keep alive~~
  - ~~fix weird keepalive clear issue, maybe do a governor thread~~
- ~~use the pid= in the m3u8 GETs~~
- ~~free up instance if it hasn't ever locked in, and it hasn't used in whatever~~
- ~~fix threading issues~~
- ~~fix nginx generation~~
- ~~no objects that could be None, anywhere~~
- maybe get all the instances ace_scraper and such into `__init__.py`
- ~~make the iptv scraper and the html scraper inherit from a common base class~~
- ~~replace `/api/streams/health/check_all`~~
- ~~only iterate through found streams for big health check~~
- ~~channel logos~~
- ~~deduplicate iptv~~
- ~~epg~~
  - ~~implement~~
  - ~~merge~~
  - ~~fetch on a schedule~~
  - ~~epg in api~~
  - ~~filtered epg, e.g. only serve an epg for streams that are available~~
  - ~~correct epg xml metadata~~
