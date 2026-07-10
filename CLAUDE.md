# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AceReStreamer (package name `acere`) scrapes AceStream links from various sources (HTML pages, IPTV m3u8 playlists, JSON APIs) and re-streams them via HLS. Clients connect via IPTV apps (Xtream Codes or m3u8) or VLC/IINA/MPV — the bundled web player was removed in the 1.3.0 refactor. Backend is FastAPI/Python; frontend is a separate React app — see [frontend/CLAUDE.md](frontend/CLAUDE.md) for frontend-specific guidance (that file is authoritative for anything under `frontend/`).

The repo is based on the [FastAPI fullstack template](https://github.com/fastapi/full-stack-fastapi-template) but has diverged significantly (see `docs/development.md`).

## Commands

Backend (run from repo root, inside the uv-managed venv):

- `uv run pytest` — run all tests. Single test: `uv run pytest tests/path/to/test_file.py::test_name`
- `uv run pytest --cov=acere --cov-report=xml --junitxml=junit.xml` — as run in CI
- `uv run ty check .` — type check (strict; mypy was dropped from dev deps in 2026-07)
- `uv run ruff format && uv run ruff check --fix` — format + lint (ruff `select = ["ALL"]`, see `pyproject.toml` for the ignore list)
- `fastapi dev --reload --port 5100 --entrypoint acere.main:app` — run the dev server (add `--host 0.0.0.0` to expose to other hosts)
- `bash scripts/run-ci-local.sh` — runs the full local CI sequence (ty, ruff, pytest, sphinx docs build, then bun lint/typecheck) — must be run inside the activated venv
- `bash scripts/generate-client.sh` — regenerates `frontend/src/client/` from the live OpenAPI schema (dumps `frontend/openapi.json` from the FastAPI app, then runs the frontend's `generate-client` and `generate-frontend-paths`). Run this after changing any API route signature, request/response model, or route path.
- `uv run sphinx-build -b html docs docs_out` — build docs (CI runs this with `--fail-on-warning`)
- CLI entry points (installed via `pyproject.toml`): `acerestreamer-scrape`, `acerestreamer-debug-get-xc-server-response`, `acerestreamer-migrate`

Frontend: see [frontend/CLAUDE.md](frontend/CLAUDE.md) (`bun run dev`, `bun run typecheck`, `bun run lint`, `bun run build-aio`).

## Testing

- `ACERE_TESTING=1` must be set before any `acere` imports — `tests/conftest.py` handles this automatically
- Test config is loaded from `tests/configs/test_valid.json`
- Sockets are disabled by default via pytest-socket (`--disable-socket`); only `127.0.0.1`, `127.0.1.1`, `::1` are allowed (`--allow-hosts` in `pyproject.toml`) — tests that need network access must mock it
- starlette ≥1.3's `TestClient` needs the `httpx2` package (in the `test` extra) or it warns and falls back to plain `httpx`

## Architecture

### Request flow / app composition (`acere/main.py`)

Two separate FastAPI apps are composed: the main `app` (API + frontend static files + IPTV routes) has `CompressMiddleware` mounted at `/`, with a second `hls_app` (HLS streaming routes only, deliberately **no** compression middleware) mounted onto it at `/`. Router breakdown, all wired in `acere/api/main.py`:

- `api_router` (prefix `API_V1_STR`) — JSON API under `acere/api/routes/api/` (ace_pool, config, health, scraper, streams, xc)
- `api_router_xc` — root-mounted Xtream Codes emulation routes (see gotcha below)
- `frontend_router` — serves the built SPA (`acere/dist/`) in all-in-one mode
- `iptv_router` — m3u8 playlist endpoints
- `hls_router` — actual HLS segment/stream proxying, mounted on the uncompressed sub-app

`lifespan()` in `main.py` is the single place that constructs and tears down every background service: `AcePool`, `AceScraper`, `RemoteSettingsFetcher`, and `AceQualityCacheHandler` (which runs its own thread, checking stream quality ~4x/day and culling dead streams). Each is registered into its `acere/instances/` singleton immediately after construction.

**Xtream Codes gotcha**: the root-mounted XC route is `/{u}/{p}/{stream}` — it swallows *any* 3-segment path, including stale/unrelated ones like `/api/v1/epg` (which now 401s instead of 404ing). Keep this in mind when adding new root-level routes or debugging unexpected 401s.

### Global singletons (`acere/instances/`)

Every long-lived service (AcePool, AceScraper, RemoteSettingsFetcher, quality handler, app path handler, config, xc category/stream caches) is wired through `acere/instances/`, one module per service, each exposing a paired `get_*()`/`set_*()` (or `setup_*()`) function backed by a `GlobalInstance[T]` (defined in `acere/instances/__init__.py`). `PLW0603` (global statement) is intentionally disabled in this package — don't try to refactor these into dependency injection. Business logic itself lives in `acere/services/`; `acere/instances/` only holds the process-wide handle to it.

### Layout

- `acere/api/routes/` — FastAPI routers: `api/` (JSON API), `hls.py` (streaming), `iptv/` (m3u8), `frontend/` (SPA serving + `generated_frontend_paths.json`, produced by `scripts/generate-client.sh`)
- `acere/services/` — business logic: `ace_pool/` (manages concurrent AceStream engine connections, `AcePool` in `pool.py`), `scraper/` (`AceScraper` in `main.py`, plus `html.py`/`iptv/`/`api.py` sub-scrapers for each source type, `name_processor.py` for stream name normalization), `xc/` (Xtream Codes response models/helpers), `ace_quality/`, `remote_settings/`, `app_paths_helper/`
- `acere/database/` — SQLModel models (`models/`), query/handler classes (`handlers/`), Alembic migrations (`migration/`, `acerestreamer-migrate` CLI)
- `acere/core/config/` — pydantic-settings config; loads from a JSON file plus `ACERE_`-prefixed env vars (`app.py` is the `AppConf` schema, e.g. `ace_address`, `ace_max_streams`)
- `acere/cli/` — the three console scripts (`scraper/`, `db_migrate/`, `get_xc_server_response/`), each a `__main__.py` module
- `tests/` mirrors the `acere/` package layout 1:1

### Known stale/empty directories

`acere/services/epg/` currently contains only `__pycache__` (no `.py` source) — a leftover from the 1.3.0 EPG removal, same pattern as the reverted `services/ace/manager.py` refactor. Don't add new code there; if you're cleaning up, it's safe to delete.

## Typing conventions

- `if TYPE_CHECKING: from x import Y else: Y = object` is a deliberate pattern used throughout to avoid circular imports while keeping runtime-safe fallbacks — not dead code, don't "simplify" it away.
- `ty` is run in strict mode; a handful of per-file rule overrides live in `pyproject.toml` under `[[tool.ty.overrides]]` for known ty false positives (documented inline with a short comment in each case).
