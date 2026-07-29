# Development

This repo is based on the FastAPI fullstack template at [this commit](https://github.com/fastapi/full-stack-fastapi-template/tree/46e86d4d4d4a35363e018db5306c80d758c59e1d). In the time since then they have changed a bunch of the libraries.

## Backend (FastAPI)

### Generate SDK and client

```bash
./scripts/generate-client.sh
```

### Run

Run development server

```bash
fastapi dev --reload --port 5100 --entrypoint acere.main:app
```

To be accessable from other hosts:

```bash
fastapi dev --reload  --host 0.0.0.0 --port 5100 --entrypoint acere.main:app
```

## Frontend (Vite + React)

Open a new vscode window in the `frontend/` folder:

```bash
code frontend/
```

```bash
bun install
```

Run development server, you can use a `.env` file if desired. The variable will affect builds, not just the dev server.

```bash
export VITE_API_URL="http://localhost:5100"  # Adjust if your backend is running elsewhere
bun run dev
```

## Docker Build

Build a combined container with both frontend and backend:

```bash
docker buildx build --network=host --file docker/Dockerfile.combined . -t acerestreamer
```

## XC (Xtream Codes) API Reference

God I hate this.

### Live Stream URLs

Depending on the IPTV client, any of these will be hit when requesting a stream. All four forms are handled by `xc_live_stream()` in `acere/api/routes/hls.py`, which picks the transport from the file extension — only `.m3u8` gets HLS, everything else (including no extension) gets MPEG-TS, matching what a real XC server does.

| Request | Transport | Seen from |
| --- | --- | --- |
| `/username/password/{stream_number}` | MPEG-TS | Smarters Player Lite (iOS), iMPlayer Android |
| `/username/password/{stream_number}.ts` | MPEG-TS | iMPlayer iOS, TiViMate, Purple Simple |
| `/username/password/{stream_number}.m3u8` | HLS | SparkleTV |
| `/live/username/password/{stream_number}.m3u8` | HLS | UHF, M3UAndroid, IPTV Smarters Pro |

The `/live/` prefix is accepted on any of these, not just the `.m3u8` form.

Note the route pattern `/{u}/{p}/{stream}` is mounted at the server root, so it swallows *any* three-segment path. An unrelated stale URL like `/api/v1/epg` will come back as a 401 from the XC auth check rather than a 404.

### Playlists

`get.php?type=m3u_plus` returns a playlist of HLS URLs; adding `output=ts` returns MPEG-TS URLs pointing back at the `/live/...` stream route above. Outside of XC, the same two playlists are served unauthenticated at `/iptv*` and `/iptv-ts*`.

### XC Listings

The JSON below is what a **real** XC server returns, kept here as protocol reference. Our emulation in `acere/services/xc/models.py` is deliberately narrower: `allowed_output_formats` is `["m3u8", "ts"]` (no rtmp), `rtmp_port` is omitted entirely, and the timezone is always UTC. Only `get_live_categories` and `get_live_streams` are implemented — the VOD and series actions return 501, and there is no EPG (removed in 1.3.0), so `epg_channel_id` is populated from `tvg_id` but nothing serves an XMLTV document.

`player_api.php?username=a&password=b`

```json
{
  "user_info": {
    "username": "a",
    "password": "b",
    "message": "Server Welcome Message",
    "auth": 1,
    "status": "Active",
    "exp_date": "1750000000",
    "is_trial": "0",
    "active_cons": "0",
    "created_at": "1740000000",
    "max_connections": "1",
    "allowed_output_formats": ["m3u8", "ts", "rtmp"]
  },
  "server_info": {
    "url": "xc.example.com",
    "port": "80",
    "https_port": "443",
    "server_protocol": "http",
    "rtmp_port": "25462",
    "timezone": "Australia/Perth",
    "timestamp_now": 1745000000,
    "time_now": "2025-04-18 18:30:20",
    "process": true
  }
}
```

`player_api.php?action=get_live_categories&username=a&password=b`

```json
[
  {
    "category_id": "22",
    "category_name": "Sports",
    "parent_id": 0
  },
  {
    "category_id": "1",
    "category_name": "Movies",
    "parent_id": 0
  },
  {
    "category_id": "4",
    "category_name": "News",
    "parent_id": 0
  }
]
```

`player_api.php?action=get_live_streams&username=a&password=b`

```json
[
  {
    "num": 1,
    "name": "My Sports Channel",
    "stream_type": "live",
    "stream_id": 4,
    "stream_icon": "",
    "epg_channel_id": "",
    "added": "1500000000",
    "is_adult": 0,
    "category_id": "22",
    "category_ids": [22],
    "custom_sid": null,
    "tv_archive": 0,
    "direct_source": "",
    "tv_archive_duration": 0
  },
  {
    "num": 2,
    "name": "My News Channel",
    "stream_type": "live",
    "stream_id": 7,
    "stream_icon": "",
    "epg_channel_id": "",
    "added": "1500000000",
    "is_adult": 0,
    "category_id": "4",
    "category_ids": [4],
    "custom_sid": null,
    "tv_archive": 0,
    "direct_source": "",
    "tv_archive_duration": 0
  }
]
```
