# Running

## 1. Docker Compose

This will include acestream, have a look at `docker-compose.yml` for configuration options. This has the AceReStreamer all-in-one container and AceStream built in.

```bash
docker compose up -d
```

## 2. From Source

Build frontend to be served by fastapi

```bash
cd frontend
bun run build-aio
```

Run production server, you can use a `.env` file if you desire

```bash
export ACERE_ENVIRONMENT=production
export ACERE_APP__ACE_ADDRESS="http://localhost:6878"
uvicorn --workers 1 acere.main:app --host 0.0.0.0 --port 5100
```

### 2a. Ace Stream

Run per the instructions on their [website](https://docs.acestream.net/products/#linux). I prefer to use docker for this.

```bash
docker run --name acestream-http-proxy -d -t -p 127.0.0.1:6878:6878 ghcr.io/martinbjeldbak/acestream-http-proxy
```

Or if you are in a network without UPnP, you will need to port forward 8621

```bash
docker run --name acestream-http-proxy -d -t -p 127.0.0.1:6878:6878 -p 8621:8621 ghcr.io/martinbjeldbak/acestream-http-proxy
```

Add `--restart unless-stopped` to the docker run command to have it restart on reboots.

## Deployment

When you run the program, a folder named `instance` will be created next to the `acere` package (the repo root when running from source, `/app/instance` in the container — which is why `docker-compose.yml` mounts `./instance:/app/instance`). This folder will contain the `config.json` file, as well as cache and the SQLite database.

To put it somewhere else, set `INSTANCE_DIR` to an absolute path. Note this one variable is **not** `ACERE_`-prefixed, since it is read before the config system starts up.

Environment variables will override the config values, and be saved to config.json. Have a look at `docker-compose.yml` for examples of environment variables.

Config variables use the `ACERE_` prefix, with `__` separating nested keys — so the `ace_address` field of the `app` section is `ACERE_APP__ACE_ADDRESS`. Top-level settings like `ACERE_EXTERNAL_URL` and `ACERE_ENVIRONMENT` take no section.

### Client URLs

Once running, streams are available over both transports:

| URL | Serves |
| --- | --- |
| `/iptv`, `/iptv.m3u`, `/iptv.m3u8` | Playlist of HLS streams |
| `/iptv-ts`, `/iptv-ts.m3u`, `/iptv-ts.m3u8` | Playlist of MPEG-TS streams |
| `/hls/{content_id}` | A single HLS stream |
| `/ts/{content_id}` | A single MPEG-TS stream |

For Xtream Codes clients, point the app at the server root and use the credentials shown on the web interface. Both playlist types are also reachable via `get.php?type=m3u_plus` (HLS) and `get.php?type=m3u_plus&output=ts` (MPEG-TS).
