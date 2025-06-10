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
- player stopped by default
