"""IPTV Proxy Streams API Blueprint."""

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from acere.api.deps import (
    get_current_active_superuser,
    get_current_user,
)
from acere.instances.epg import get_epg_handler
from acere.instances.iptv_streams import get_iptv_streams_db_handler
from acere.services.scraper.models import FoundIPTVStreamAPI
from acere.utils.api_models import MessageResponseModel
from acere.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/iptv/streams", tags=["IPTV Streams"], dependencies=[Depends(get_current_user)])


@router.get("/")
def streams() -> list[FoundIPTVStreamAPI]:
    """API endpoint to get all IPTV proxy streams."""
    handler = get_iptv_streams_db_handler()
    db_streams = handler.get_streams_cached()

    epg_handler = get_epg_handler()
    result: list[FoundIPTVStreamAPI] = []
    for stream in db_streams:
        program_title, program_description = epg_handler.get_current_program(stream.tvg_id)
        result.append(
            FoundIPTVStreamAPI(
                title=stream.title,
                slug=stream.slug,
                upstream_url=stream.upstream_url,
                source_name=stream.source_name,
                tvg_id=stream.tvg_id,
                tvg_logo=stream.tvg_logo,
                group_title=stream.group_title,
                last_scraped_time=stream.last_scraped_time,
                program_title=program_title,
                program_description=program_description,
            )
        )

    return result


@router.get("/slug/{slug}")
def by_slug(slug: str) -> FoundIPTVStreamAPI:
    """API endpoint to get a specific IPTV stream by slug."""
    handler = get_iptv_streams_db_handler()
    stream = handler.get_by_slug(slug)
    if not stream:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="IPTV stream not found")

    epg_handler = get_epg_handler()
    program_title, program_description = epg_handler.get_current_program(stream.tvg_id)

    return FoundIPTVStreamAPI(
        title=stream.title,
        slug=stream.slug,
        upstream_url=stream.upstream_url,
        source_name=stream.source_name,
        tvg_id=stream.tvg_id,
        tvg_logo=stream.tvg_logo,
        group_title=stream.group_title,
        last_scraped_time=stream.last_scraped_time,
        program_title=program_title,
        program_description=program_description,
    )


@router.delete("/slug/{slug}", dependencies=[Depends(get_current_active_superuser)])
def delete_by_slug(slug: str) -> MessageResponseModel:
    """API endpoint to delete an IPTV stream by slug."""
    handler = get_iptv_streams_db_handler()
    deleted = handler.delete_by_slug(slug)
    if not deleted:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="IPTV stream not found")

    return MessageResponseModel(message="IPTV stream deleted successfully")
