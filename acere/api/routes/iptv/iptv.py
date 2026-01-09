# """Blueprint for IPTV functionality in Ace Streamer."""

from typing import Annotated

from fastapi import APIRouter, Query, Response

from acere.core.stream_token import verify_stream_token
from acere.instances.scraper import get_ace_scraper
from acere.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Media/IPTV"])


# region /iptv
@router.get("/iptv", name="iptv_m3u8_1")
@router.get("/iptv.m3u", name="iptv_m3u_2")
@router.get("/iptv.m3u8", name="iptv_m3u8_3")
def iptv(token: Annotated[str, Query()] = "") -> Response:
    """Render the IPTV M3U8 Playlist."""
    verify_stream_token(token)

    ace_scraper = get_ace_scraper()
    m3u8 = ace_scraper.get_streams_as_iptv(token=token)

    return Response(
        content=m3u8,
        media_type="application/vnd.apple.mpegurl",
    )
