# acerestreamer

A webapp that scrapes AceStream links from various sources and re-streams them via HLS or MPEG-TS.

[![Check](https://github.com/kism/AceReStreamer/actions/workflows/check.yml/badge.svg)](https://github.com/kism/AceReStreamer/actions/workflows/check.yml)
[![CheckType](https://github.com/kism/AceReStreamer/actions/workflows/check_types.yml/badge.svg)](https://github.com/kism/AceReStreamer/actions/workflows/check_types.yml)
[![Test](https://github.com/kism/AceReStreamer/actions/workflows/test.yml/badge.svg)](https://github.com/kism/AceReStreamer/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/kism/AceReStreamer/graph/badge.svg?token=FPGDA0ODT7)](https://codecov.io/gh/kism/AceReStreamer)

## Features

- Scrape HTML, IPTV (m3u8) and API sources for ace streams.
- Re-streams via HLS or MPEG-TS.
  - Intended to be used with Dispatcharr or m3u-editor
  - IPTV Clients (UHF, Tivimate, IPTV Smarters, etc) via Xtream Code or m3u8
  - VLC, IINA, MPV
- Web admin interface for managing sources and streams.
- FastAPI backend, React frontend, type checking enforced.

EPG support, user management and the webplayer have been removed as Dispatcharr supports all of these much better.

This can either be used as an AceStream to IPTV bridge in your home network, or as a source for Dispatcharr or m3u-editor.

## Run

For full details, see the [docs](https://acerestreamer.readthedocs.io/en/latest/).

Easiest way is via docker compose:

- Copy `docker-compose.yml` to your server
- Edit the environment variables defined in `docker-compose.yml` to your needs.
- Run with:

  ```bash
  docker compose up -d
  ```
