# acestreamwebplayer

[![Check](https://github.com/kism/acestream-webplayer/actions/workflows/check.yml/badge.svg)](https://github.com/kism/acestream-webplayer/actions/workflows/check.yml)
[![CheckType](https://github.com/kism/acestream-webplayer/actions/workflows/check_types.yml/badge.svg)](https://github.com/kism/acestream-webplayer/actions/workflows/check_types.yml)
[![Test](https://github.com/kism/acestream-webplayer/actions/workflows/test.yml/badge.svg)](https://github.com/kism/acestream-webplayer/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kism/acestream-webplayer/graph/badge.svg?token=FPGDA0ODT7)](https://codecov.io/gh/kism/acestream-webplayer)

## Prerequisites

Install uv <https://docs.astral.sh/uv/getting-started/installation/>

## Run

### Prerequsites

Run ace stream, I use docker

```bash
docker run -t -p 6878:6878 ghcr.io/martinbjeldbak/acestream-http-proxy
```

### Run Dev

```bash
uv venv
source .venv/bin/activate
uv sync
flask --app acestreamwebplayer run --port 5100
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
    --call acestreamwebplayer:create_app
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

- ~~less recursion in patient search i think~~
- ~~scraper list~~
  - ~~populate quality~~
  - ~~cache the quality~~
- scraper global settings
  - frequency
  - ~~forbidden titles~~
- ~~actually set stream id in js~~
- ~~use unauthorised for endpoints that require auth~~
- ~~player stopped by default~~
- ~~add about page~~
- ~~add table sorting~~
- ~~iptv support~~
- ~~instructions page~~
- ~~figure out types for get_streams and get_streams_flat~~
  - ~~pydantic to replace typedict?~~
- /health endpoint
- api reference
- ~~publish~~
  - ~~streams/flat~~
  - ~~streams/by_site~~
- pytest
- vitest?
- iptv guide
- cache the sources
- iptv api
- chromecast / airplay support
- breadcrumb
