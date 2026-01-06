from fastapi import APIRouter

from acere.instances.config import settings

from .routes import (
    ace_pool,
    config,
    epg,
    health,
    login,
    private,
    scraper,
    streams,
    users,
    xc,
)
from .routes_frontend import frontend
from .routes_media import (
    epg as epg_xml,
)
from .routes_media import (
    iptv as iptv_m3u8,
)
from .routes_media import (
    stream as stream_media,
)

api_router = APIRouter()
api_router.include_router(ace_pool.router)
api_router.include_router(config.router)
api_router.include_router(epg.router)
api_router.include_router(health.router)
api_router.include_router(login.router)
api_router.include_router(scraper.router)
api_router.include_router(streams.router)
api_router.include_router(users.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)

api_router_xc = APIRouter()
api_router_xc.include_router(xc.router)

media_router = APIRouter()
media_router.include_router(stream_media.router)
media_router.include_router(iptv_m3u8.router)
media_router.include_router(epg_xml.router)

frontend_router = APIRouter()
frontend_router.include_router(frontend.router)
