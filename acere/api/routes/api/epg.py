"""Blueprint for EPG API Endpoints."""

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from acere.api.deps import (
    get_current_active_superuser,
    get_current_user,
)
from acere.core.config import EPGInstanceConf
from acere.instances.config import settings
from acere.instances.epg import get_epg_handler
from acere.services.epg.models import EPGApiHandlerHealthResponse, TVGEPGMappingsResponse
from acere.utils.helpers import slugify

router = APIRouter(
    prefix="/epg",
    tags=["EPG"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/health")
def epg_health() -> EPGApiHandlerHealthResponse:
    """Get the list of EPGs w/health."""
    return get_epg_handler().get_epgs_api()


@router.get("/")
def get_epgs() -> list[EPGInstanceConf]:
    """Get the list of EPG configurations."""
    return settings.epgs


@router.get("/slug/{slug}")
def get_epg(slug: str) -> EPGInstanceConf:
    """Get a specific EPG configuration by slug."""
    epg = next((epg for epg in settings.epgs if slugify(epg.url.host) == slug), None)
    if epg is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="EPG not found",
        )
    return epg


@router.post("/", dependencies=[Depends(get_current_active_superuser)])
def add_epg(body_json: EPGInstanceConf | list[EPGInstanceConf]) -> None:
    """Add a new EPG source."""
    if not body_json:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="json is empty",
        )

    epg_handler = get_epg_handler()
    if not isinstance(body_json, list):
        body_json = [body_json]

    for epg_instance in body_json:
        settings.add_epg(epg_instance)

    epg_handler.update_epgs(settings.epgs)


@router.delete("/slug/{slug}", dependencies=[Depends(get_current_active_superuser)])
def delete_epg(slug: str) -> None:
    """Delete an EPG source by slug."""
    epg_handler = get_epg_handler()

    success = settings.remove_epg(slug)
    if not success:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="EPG not found",
        )

    epg_handler.update_epgs(settings.epgs)


@router.get("/tvg-ids")
def tvg_epg_mappings() -> TVGEPGMappingsResponse:
    """Get the mapping of TVG IDs to their source EPG URLs."""
    return get_epg_handler().get_tvg_epg_mappings()
