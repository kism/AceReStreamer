# Development

This repo is based on the FastAPI fullstack template at [this commit](https://github.com/fastapi/full-stack-fastapi-template/tree/46e86d4d4d4a35363e018db5306c80d758c59e1d). In the time since then they have changed a bunch of the libraries.

## Backend (FastAPI)

### Generate SDK and clinent

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
export VITE_BACKEND_URL="http://localhost:5100"  # Adjust if your backend is running elsewhere
bun run dev
```

## Docker Build

Build a combined container with both frontend and backend:

```bash
docker buildx build --network=host --file docker/Dockerfile.combined . -t acerestreamer
```

### Separate Frontend and Backend Container

Build the backend and frontend containers separately:

```bash
docker buildx build --file docker/Dockerfile.backend . -t acerestreamer-backend
docker buildx build --build-arg VITE_API_URL="https://api.example.com" --file docker/Dockerfile.frontend ./frontend -t acerestreamer-frontend
```

## XC (Xtream Codes) API Reference

God I hate this.

### Live Stream URLs

```text
/username/password/{stream_number}
/username/password/{stream_number}.m3u8
/username/password/{stream_number}.ts
/live/username/password/{stream_number}.m3u8
```

Depending on the IPTV client, any of these will be hit when requesting a stream.

### XC Listings

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
