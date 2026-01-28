"""Main Stream Site Blueprint."""

from fastapi import APIRouter, Depends, HTTPException

from acere.api.deps import (
    get_current_active_superuser,
    get_current_user,
)
from acere.instances.ace_quality import get_quality_handler
from acere.instances.ace_streams import get_ace_streams_db_handler
from acere.instances.epg import get_epg_handler
from acere.services.ace_quality import Quality
from acere.services.scraper.models import FoundAceStreamAPI
from acere.utils.api_models import MessageResponseModel
from acere.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/streams", tags=["Streams"], dependencies=[Depends(get_current_user)])


# region /api/stream(s)
@router.get("/content_id/{content_id}")
def by_content_id(content_id: str) -> FoundAceStreamAPI:
    """API endpoint to get a specific stream by Ace ID."""
    handler = get_ace_streams_db_handler()
    stream = handler.get_by_content_id(content_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    quality_handler = get_quality_handler()
    quality = quality_handler.get_quality(content_id)

    epg_handler = get_epg_handler()
    program_title, program_description = epg_handler.get_current_program(stream.tvg_id)

    return FoundAceStreamAPI(
        title=stream.title,
        content_id=stream.content_id,
        infohash=stream.infohash,
        tvg_id=stream.tvg_id,
        tvg_logo=stream.tvg_logo,
        quality=quality.quality,
        has_ever_worked=quality.has_ever_worked,
        m3u_failures=quality.m3u_failures,
        program_title=program_title,
        program_description=program_description,
        last_scraped_time=stream.last_scraped_time,
    )


@router.delete("/content_id/{content_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_by_content_id(content_id: str) -> MessageResponseModel:
    """API endpoint to delete a specific stream by Ace ID."""
    handler = get_ace_streams_db_handler()
    deleted = handler.delete_by_content_id(content_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Stream not found")

    return MessageResponseModel(message="Stream deleted successfully")


@router.get("/")
def streams() -> list[FoundAceStreamAPI]:
    """API endpoint to get the flat streams."""
    handler = get_ace_streams_db_handler()
    streams = handler.get_streams_cached()

    streams_api: list[FoundAceStreamAPI] = []
    epg_handler = get_epg_handler()
    for stream in streams:
        quality_handler = get_quality_handler()
        quality = quality_handler.get_quality(stream.content_id)

        program_title, program_description = epg_handler.get_current_program(stream.tvg_id)

        streams_api.append(
            FoundAceStreamAPI(
                title=stream.title,
                content_id=stream.content_id,
                infohash=stream.infohash,
                tvg_id=stream.tvg_id,
                tvg_logo=stream.tvg_logo,
                quality=quality.quality,
                has_ever_worked=quality.has_ever_worked,
                m3u_failures=quality.m3u_failures,
                program_title=program_title,
                program_description=program_description,
                last_scraped_time=stream.last_scraped_time,
            )
        )

    return streams_api


@router.get("/health")
def health() -> dict[str, Quality]:
    """API endpoint to get the streams."""
    quality_handler = get_quality_handler()
    return quality_handler.get_all()


@router.post("/check", dependencies=[Depends(get_current_active_superuser)])
async def check() -> MessageResponseModel:
    """API endpoint to attempt to check all streams health."""
    handler = get_quality_handler()
    started = await handler.check_missing_quality()

    logger.info("/api/sources/check Health check started: %s", started)

    if started:
        response = MessageResponseModel(message="Health check started")
    else:
        response = MessageResponseModel(message="Health check already running")

    return response
