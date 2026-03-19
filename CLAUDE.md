# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AceReStreamer scrapes AceStream links from various sources and re-streams them via HLS. It has a **FastAPI backend** (`acere/`) and a **React frontend** (`frontend/`). The backend requires Python 3.14+ and uses `uv` for package management; the frontend uses `bun`.

## Common Commands

### Backend (run from repo root, inside the venv)

```bash
uv sync --extra test --extra type --extra lint  # Install all deps
uv run uvicorn acere.main:app --port 5100       # Run dev server

uv run pytest                                   # Run all tests
uv run pytest tests/path/to/test_file.py        # Run a single test file
uv run pytest -k "test_name"                    # Run a specific test

uv run mypy                                     # Type check with mypy
uv run ty check .                               # Type check with ty

uv run ruff format                              # Format code
uv run ruff check --fix                         # Lint + auto-fix

uv run sphinx-build --fail-on-warning -b html docs docs_out  # Build docs
```

### Frontend (run from `frontend/`)

```bash
bun install          # Install deps
bun run dev          # Dev server (proxies to backend at localhost:5100)
bun run build-aio    # Build and output into acere/dist/ (all-in-one mode)
bun run typecheck    # TypeScript type check
bun run lint         # Biome lint + format
bun run test:e2e     # Playwright end-to-end tests
```

### Generate API client (run from repo root, inside the venv)

```bash
bash scripts/generate-client.sh   # Regenerates frontend/src/client/ from backend OpenAPI spec
```

### Run all CI checks locally

```bash
bash scripts/run-ci-local.sh
```

## Architecture

### Backend package: `acere/`

**`acere/main.py`** — FastAPI app entry point. The `lifespan()` context manager starts all background services on startup and stops them on shutdown. There are two separate FastAPI apps: `app` (with compression) and `hls_app` (no compression, mounted at `/`).

**`acere/instances/`** — Global singleton pattern. Each service (config, ace*pool, ace_quality, ace_streams, epg, scraper, xc_category, paths, remote_settings) has a module-level `_private` variable with `get*_()`/`set\__()`accessors. Services are instantiated in`main.py:lifespan()`and stored here. Ruff rule`PLW0603` (no globals) is disabled only in this package.

**`acere/services/`** — Business logic services:

- `ace/pool/` — Manages a pool of AceStream HTTP proxy instances. Runs a background thread (`ace_poolboy`) to health-check and clean up stale instances.
- `ace/quality/` — Stream quality checking.
- `scraper/` — Scrapes AceStream content IDs from HTML pages, IPTV playlists, and APIs.
- `epg/` — Electronic Program Guide sourcing and matching.
- `xc/` — Xtream Codes protocol support.
- `remote_settings/` — Fetches config from a remote URL.

**`acere/api/routes/`** — FastAPI routers split into:

- `api/` — REST API endpoints (prefixed `/api/v1/`)
- `hls.py` — HLS proxying (no compression middleware)
- `iptv/` — IPTV m3u8 and EPG XML endpoints
- `frontend/` — Serves the built React SPA

**`acere/database/`** — SQLModel models with SQLite. Alembic migrations in `migration/versions/`. Handlers (`handlers/`) provide service-layer access to each table. `init.py` sets up the engine.

**`acere/config/`** — Pydantic-settings `AceReStreamerConf`. Config is loaded from a JSON file in the `instance/` directory and environment variables (prefix `ACERE_`, nested delimiter `__`). Config is written back to disk on startup. The `MigratingJsonConfigSettingsSource` handles old config format migration.

**`acere/cli/`** — CLI entry points: `scraper`, `password_reset`, `get_xc_server_response`, `db_migrate`.

### Frontend: `frontend/src/`

React 19 + TypeScript, TanStack Router (file-based routing), TanStack Query, Chakra UI v3. API client code in `src/client/` is **auto-generated** from the backend's OpenAPI spec — do not edit those files manually. Routes live in `src/routes/`. Global theme customizations in `src/theme/`.

### Key integration points

- The backend serves the built frontend (`acere/dist/`) in "all-in-one" mode. The list of frontend routes is generated into `acere/api/routes/frontend/generated_frontend_paths.json` by `bun run generate-frontend-paths`.
- `IN_OPEN_API_MODE=true` env var suppresses startup output so the OpenAPI JSON can be extracted cleanly during client generation.
- Docker compose: `acestream-http-proxy` (port 6878) + `acerestreamer` (port 5100).

## Testing Notes

- Tests set `ACERE_TESTING=1` and `INSTANCE_DIR` env vars **before** importing any `acere` modules. See `tests/conftest.py` — the import ordering is critical.
- Network sockets are disabled in tests by default (`--disable-socket`); hosts `127.0.0.1` and `127.0.1.1` are allowed.
- Test config is copied from `tests/configs/test_valid.json` into a `tempfile.mkdtemp()` directory.
- The `db` fixture is session-scoped; `client` fixture is module-scoped.

## Type Checking Notes

- Strict mypy and `ty` are both enforced.
- The `TYPE_CHECKING` guard pattern is used extensively to break circular import cycles while retaining type safety — the pattern `if TYPE_CHECKING: from x import Y else: Y = object` is intentional throughout the codebase.
- Pydantic/SQLModel base classes that need runtime evaluation are listed in `[tool.ruff.lint.flake8-type-checking] runtime-evaluated-base-classes`.
