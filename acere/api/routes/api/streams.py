"""Combined Streams API Blueprint."""

from fastapi import APIRouter, Depends

from acere.api.deps import get_current_user
from acere.instances.ace_streams import get_ace_streams_db_handler
from acere.instances.config import settings
from acere.instances.epg import get_epg_handler
from acere.instances.iptv_streams import get_iptv_streams_db_handler
from acere.instances.quality import get_quality_handler
from acere.services.scraper.models import CombinedStreamAPI

router = APIRouter(prefix="/streams", tags=["Streams"], dependencies=[Depends(get_current_user)])


@router.get("/")
def streams() -> list[CombinedStreamAPI]:
    """API endpoint to get all streams (ace and IPTV combined)."""
    epg_handler = get_epg_handler()
    external_url = settings.EXTERNAL_URL
    result: list[CombinedStreamAPI] = []

    # Ace streams
    ace_handler = get_ace_streams_db_handler()
    quality_handler = get_quality_handler()
    for stream in ace_handler.get_streams_cached():
        quality = quality_handler.get_quality(stream.content_id)
        program_title, program_description = epg_handler.get_current_program(stream.tvg_id)
        result.append(
            CombinedStreamAPI(
                stream_type="ace",
                title=stream.title,
                stream_url=f"{external_url}/hls/ace/{stream.content_id}",
                tvg_id=stream.tvg_id,
                tvg_logo=stream.tvg_logo,
                group_title=stream.group_title,
                last_scraped_time=stream.last_scraped_time,
                program_title=program_title,
                program_description=program_description,
                quality=quality.quality,
            )
        )

    # IPTV proxy streams
    iptv_handler = get_iptv_streams_db_handler()
    for iptv_stream in iptv_handler.get_streams_cached():
        quality = quality_handler.get_quality(iptv_stream.upstream_url)
        program_title, program_description = epg_handler.get_current_program(iptv_stream.tvg_id)
        result.append(
            CombinedStreamAPI(
                stream_type="iptv",
                title=iptv_stream.title,
                stream_url=f"{external_url}/hls/web/{iptv_stream.slug}",
                tvg_id=iptv_stream.tvg_id,
                tvg_logo=iptv_stream.tvg_logo,
                group_title=iptv_stream.group_title,
                last_scraped_time=iptv_stream.last_scraped_time,
                program_title=program_title,
                program_description=program_description,
                quality=quality.quality,
            )
        )

    return result
