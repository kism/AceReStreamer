"""IPTV Proxy Scraper API Blueprint."""

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from acere.api.deps import (
    get_current_active_superuser,
    get_current_user,
)
from acere.config.iptv import IPTVSourceM3U8, IPTVSourceXtream
from acere.instances.config import settings
from acere.instances.iptv_proxy import get_iptv_proxy_manager
from acere.services.scraper.models import IPTVSourceApi
from acere.utils.api_models import MessageResponseModel
from acere.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/iptv/scraper", tags=["IPTV Scraper"])


@router.get("/", dependencies=[Depends(get_current_user)])
def sources() -> list[IPTVSourceApi]:
    """API endpoint to list all IPTV proxy sources."""
    result = [IPTVSourceApi.from_xtream(source) for source in settings.iptv.xtream]
    result.extend(IPTVSourceApi.from_m3u8(source) for source in settings.iptv.m3u8)
    return result


@router.get("/{source_name}", dependencies=[Depends(get_current_user)])
def source(source_name: str) -> IPTVSourceApi:
    """API endpoint to get a single IPTV proxy source by name."""
    for xtream_source in settings.iptv.xtream:
        if xtream_source.name == source_name:
            return IPTVSourceApi.from_xtream(xtream_source)
    for m3u8_source in settings.iptv.m3u8:
        if m3u8_source.name == source_name:
            return IPTVSourceApi.from_m3u8(m3u8_source)

    raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="IPTV source not found")


@router.post("/", dependencies=[Depends(get_current_active_superuser)])
def add_source(body_json: IPTVSourceApi | list[IPTVSourceApi]) -> MessageResponseModel:
    """API endpoint to add IPTV proxy sources."""
    errors: list[str] = []
    if not body_json:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="json is empty")

    if not isinstance(body_json, list):
        body_json = [body_json]

    for n, item in enumerate(body_json):
        if item.type == "xtream":
            if not item.username or not item.password:
                errors.append(f"Item {n}: Xtream source requires username and password")
                continue
            xtream = IPTVSourceXtream(
                name=item.name,
                url=item.url,
                username=item.username,
                password=item.password,
                title_filter=item.title_filter,
                category_filter=item.category_filter,
                max_active_streams=item.max_active_streams,
            )
            success, msg = settings.iptv.add_xtream_source(xtream)
        elif item.type == "m3u8":
            m3u8 = IPTVSourceM3U8(
                name=item.name,
                url=item.url,
                title_filter=item.title_filter,
                category_filter=item.category_filter,
                max_active_streams=item.max_active_streams,
            )
            success, msg = settings.iptv.add_m3u8_source(m3u8)
        else:
            success = False
            msg = "Invalid source type"

        if not success:
            errors.append(f"Item {n}: {msg}")

    if errors:
        msg = "Errors adding sources" if len(errors) > 1 else "Error adding source"
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=msg)

    msg = "Sources added successfully" if len(body_json) > 1 else "Source added successfully"

    settings.write_config()
    get_iptv_proxy_manager().start_scrape_thread()

    return MessageResponseModel(message=msg)


@router.delete("/{source_name}", dependencies=[Depends(get_current_active_superuser)])
def remove_source(source_name: str) -> MessageResponseModel:
    """API endpoint to remove an IPTV proxy source."""
    success, msg = settings.iptv.remove_source(source_name)
    if not success:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=msg)

    settings.write_config()

    return MessageResponseModel(message=msg)
