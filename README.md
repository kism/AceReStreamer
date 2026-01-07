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
docker run -d -t -p 127.0.0.1:6878:6878 ghcr.io/martinbjeldbak/acestream-http-proxy
# Or if you are in a situation without UPnP, you will need to port forward 8621
docker run -d -t -p 127.0.0.1:6878:6878 -p 8621:8621 ghcr.io/martinbjeldbak/acestream-http-proxy
```

Or even better, use docker compose

```bash
docker compose up -d
```

### Frontend

```bash
cd frontend
nvm use
npm install
```

Run frontend dev server

```bash
npm run dev
```

Build frontend to be served by the backend. You will need to ensure that `VITE_API_URL` in `.env` is not set, to ensure portability.

```bash
npm run build-dev
```

### Backend

```bash
uv venv
uv sync
```

Run development server

```bash
fastapi dev --reload --port 5100 --entrypoint acere.main:app
fastapi dev --reload  --host 0.0.0.0 --port 5100 --entrypoint acere.main:app # To be accessable from other hosts
```

Run production server

```bash
uvicorn --workers 1 acere.main:app --host 0.0.0.0 --port 5100
```

If you want to serve the frontend with fastapi, in `config.json` set `FRONTEND_HOST: ""`

If you want to use the Vite dev server, or another server to serve the frontend, in `config.json` set `FRONTEND_HOST: "http://localhost:5173"`

### Docker

```bash
docker buildx build --file docker/Dockerfile.combined . -t acerestreamer
```

```bash
docker buildx build --file docker/Dockerfile.backend . -t acerestreamer-backend
docker buildx build --build-arg VITE_API_URL="https://api.example.com" --file docker/Dockerfile.frontend ./frontend -t acerestreamer-frontend
```

### Features

### Apps that don't work

see iptv.html.j2

## todo

- No auth mode
- consistent theming
  - button sizes
  - inconsistent close button
- stream restarting in hls.js
- stricter ruff rules
- readme
- big cleanup
- async everything?
- name the loggers
- case insensitive username
