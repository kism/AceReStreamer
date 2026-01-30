# Running

## 1. Docker Compose

This will inclue acestream, have a look at `docker-compose.yml` for configuration options. This has the AceReStreamer all-in-one contiainer and AceStream built in.

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
export ACERE_FRONTEND_HOST="example.com"  # Set to your domain
export ACERE_FIRST_SUPERUSER_USERNAME="admin"
export ACERE_FIRST_SUPERUSER_PASSWORD="" # This will only set the password on first run, if empty a random password will be generated and printed in the logs
uvicorn --workers 1 acere.main:app --host 0.0.0.0 --port 5100
```

### 2a. Ace Stream

Run per the instructions on their [website](https://docs.acestream.net/products/#linux). I prefer to use docker for this.

```bash
docker run -d -t -p 127.0.0.1:6878:6878 ghcr.io/martinbjeldbak/acestream-http-proxy
```

Or if you are in a network without UPnP, you will need to port forward 8621

```bash
docker run -d -t -p 127.0.0.1:6878:6878 -p 8621:8621 ghcr.io/martinbjeldbak/acestream-http-proxy
```

## Deployment

When you run the program, a folder named `instance` will be created in the working directory. This folder will contain the `config.json` file, as well as cache and the SQLite database.

Environment vaiables will override the config values, and be saved to config.json. Have a look at `docker-compose.yml` for examples of environment variables.
