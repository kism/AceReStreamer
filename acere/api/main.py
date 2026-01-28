from fastapi import APIRouter

from acere.instances.config import settings

from .routes import frontend, hls
from .routes.api import (
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
from .routes.iptv import (
    epg as epg_xml,
)
from .routes.iptv import (
    iptv as iptv_m3u8,
)

api_router = APIRouter()
api_router.include_router(ace_pool.router)
api_router.include_router(epg.router)
api_router.include_router(health.router)
api_router.include_router(login.router)
api_router.include_router(scraper.router)
api_router.include_router(streams.router)
api_router.include_router(users.router)
api_router.include_router(config.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)

api_router_xc = APIRouter()
api_router_xc.include_router(xc.router)

hls_router = APIRouter()
hls_router.include_router(hls.router)

frontend_router = APIRouter()
frontend_router.include_router(frontend.router)

iptv_router = APIRouter()
iptv_router.include_router(epg_xml.router)
iptv_router.include_router(iptv_m3u8.router)
