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
docker run -t -p 6878:6878 ghcr.io/martinbjeldbak/acestream-http-proxy
# Or maybe it's better to also allow the torrent port?
docker run -t -p 6878:6878 -p 8621:8621 ghcr.io/martinbjeldbak/acestream-http-proxy
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

## todo structure

### Pages

| path        | description                      |
| ----------- | -------------------------------- |
| /           | login page                       |
| /stream     | stream webplayer                 |
| /hls        | reverse proxy for ace m3u8 files |
| /ace/c      | proxy for ace stream .ts files   |
| /iptv       | iptv m3u8 playlist               |
| /info/guide | Main guide page                  |
| /info/iptv  | IPTV guide page                  |
| /info/about | about / health check page        |

### API Endpoints

| path                 | method | description               |
| -------------------- | ------ | ------------------------- |
| /api/authenticate    | POST   | authenticate endpoint     |
| /api/authenticate    | GET    | get authentication status |
| /api/streams/flat    | GET    | get all streams flat      |
| /api/streams/by_site | GET    | get all streams by site   |
| /api/streams/health  | GET    | stream ids w/health       |
| /api/stream/{id}     | GET    | get stream by id          |

## todo

- login page
- /health endpoint
- api reference
- pytest
- vitest?
- cache the sources
- iptv api
  - more on the iptv guide
- chromecast / airplay support
- investigate .copy()
- actually fetch in a thread

- ~~publish~~
  - ~~streams/flat~~
  - ~~streams/by_site~~
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
- investigate if I need to reload nginx
