import os
import random
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI
from rich import traceback
from sqlmodel import Session, select
from starlette.middleware.cors import CORSMiddleware
from starlette_compress import CompressMiddleware

from acere.api.main import api_router, api_router_xc, frontend_router, hls_router, iptv_router
from acere.constants import API_V1_STR, SETTINGS_FILE
from acere.core.db import engine, init_db
from acere.instances.ace_pool import set_ace_pool
from acere.instances.config import settings
from acere.instances.scraper import set_ace_scraper
from acere.services.ace_pool.pool import AcePool
from acere.services.scraper import AceScraper
from acere.utils.logger import get_logger, setup_logger
from acere.version import PROGRAM_NAME, __version__

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from fastapi.routing import APIRoute
else:
    AsyncIterator = object
    APIRoute = object


# Don't put anything on stdout if we are generating openapi json
IN_OPEN_API_MODE: bool = os.getenv("IN_OPEN_API_MODE", "false").lower() == "true"

# Lock file to detect multiple worker processes
WORKER_LOCK_FILE = Path("/tmp/acerestreamer_worker.lock")  # noqa: S108 Contents never get read


# Check for multiple workers - this application does not support multiple workers
# due to singleton instances and shared state
def check_single_worker() -> None:
    """Check that only one worker is running."""
    logger = get_logger(__name__)
    if WORKER_LOCK_FILE.exists():
        msg = [
            ("This application does not support multiple workers. Another worker instance is already running. "),
            "Please run with --workers 1 or remove the --workers flag.",
            "Or the application crashed previously and the lock file was not removed.",
        ]
        logger.critical("\n".join(msg))

    # Create lock file
    try:
        WORKER_LOCK_FILE.write_text(str(os.getpid()))
    except Exception as e:  # noqa: BLE001 Catch all to prevent crash on startup
        msg_str = f"Could not create worker lock file: {e}"
        logger.critical(msg_str)


if not IN_OPEN_API_MODE:
    traceback.install()

    settings.write_config(SETTINGS_FILE)
    setup_logger(settings=settings.logging)
    setup_logger(settings=settings.logging, in_logger="uvicorn.error")

    check_single_worker()

    logger = get_logger(__name__)

    FRONTEND_INFO = (
        "Serving internally" if settings.FRONTEND_HOST == "" else f"Frontend server: {settings.FRONTEND_HOST}"
    )

    msg = f""">>>
-------------------------------------------------------------------------------
{PROGRAM_NAME}
Version: {__version__}
Config file: {SETTINGS_FILE.absolute()}
Environment: {settings.ENVIRONMENT.capitalize()}
Frontend: {FRONTEND_INFO}
External URL: {settings.EXTERNAL_URL}
-------------------------------------------------------------------------------"""

    logger.info(msg)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan - startup and shutdown."""
    # Startup
    instance_id = str(random.randbytes(4).hex())  # noqa: S311 Not crypto related
    ace_pool = AcePool(instance_id=instance_id)
    set_ace_pool(ace_pool)
    ace_scraper = AceScraper(instance_id=instance_id)
    set_ace_scraper(ace_scraper)

    yield
    # Shutdown - cleanup lock file
    if WORKER_LOCK_FILE.exists():
        with suppress(Exception):
            WORKER_LOCK_FILE.unlink()


with Session(engine) as session:
    session.exec(select(1))
    init_db(session)

app = FastAPI(
    title=PROGRAM_NAME,
    openapi_url=f"{API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)
app.add_middleware(CompressMiddleware)
app.include_router(api_router, prefix=API_V1_STR)
app.include_router(api_router_xc)
app.include_router(frontend_router)
app.include_router(iptv_router)

hls_app = FastAPI()
hls_app.include_router(hls_router)
app.mount("/", hls_app)


# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        middleware_class=CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


if IN_OPEN_API_MODE:
    defaults = settings.force_load_defaults()
    settings.EXTERNAL_URL = defaults.EXTERNAL_URL
