import os
import random
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from rich import traceback
from sqlmodel import Session, select
from starlette.middleware.cors import CORSMiddleware
from starlette_compress import CompressMiddleware

from acere.api.main import api_router, api_router_xc, frontend_router, hls_router, iptv_router
from acere.constants import API_V1_STR, SETTINGS_FILE
from acere.database.init import engine, init_db
from acere.instances.ace_pool import set_ace_pool
from acere.instances.config import settings
from acere.instances.epg import set_epg_handler
from acere.instances.remote_settings import set_remote_settings_fetcher
from acere.instances.scraper import set_ace_scraper
from acere.services.ace_pool.pool import AcePool
from acere.services.epg import EPGHandler
from acere.services.remote_settings import RemoteSettingsFetcher
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


if not IN_OPEN_API_MODE:
    traceback.install()

    settings.write_config(SETTINGS_FILE)
    setup_logger(settings=settings.logging)
    setup_logger(settings=settings.logging, in_logger="uvicorn.error")

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
    # Initialize database
    with Session(engine) as session:
        session.exec(select(1))
        init_db(session)

    instance_id = str(random.randbytes(4).hex())  # noqa: S311 Not crypto related

    # Pool
    ace_pool = AcePool(instance_id=instance_id)
    set_ace_pool(ace_pool)

    # Scraper
    ace_scraper = AceScraper(instance_id=instance_id)
    set_ace_scraper(ace_scraper)

    # Settings Fetcher
    remote_settings_fetcher = RemoteSettingsFetcher(instance_id=instance_id)
    set_remote_settings_fetcher(remote_settings_fetcher)

    # EPG Handler
    epg_handler = EPGHandler(instance_id=instance_id)
    set_epg_handler(epg_handler)

    yield

    handlers: list[AceScraper | AcePool | RemoteSettingsFetcher | EPGHandler] = [
        ace_pool,
        ace_scraper,
        remote_settings_fetcher,
        epg_handler,
    ]
    for handler in handlers:
        handler.stop_all_threads()

    logger.info("End of application lifespan? [%s]", instance_id)


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
