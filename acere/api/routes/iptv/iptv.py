# """Blueprint for IPTV functionality in Ace Streamer."""

from typing import Annotated

from fastapi import APIRouter, Query, Response
from pydantic import HttpUrl

from acere.core.stream_token import verify_stream_token
from acere.instances.ace_streams import get_ace_streams_db_handler
from acere.instances.config import settings
from acere.instances.iptv_streams import get_iptv_streams_db_handler
from acere.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Media/IPTV"])


@router.get("/iptv", name="iptv_m3u8_1")
@router.get("/iptv.m3u", name="iptv_m3u_2")
@router.get("/iptv.m3u8", name="iptv_m3u8_3")
def iptv(token: Annotated[str, Query()] = "") -> Response:
    """Render the unified IPTV M3U8 Playlist (ace + IPTV proxy streams)."""
    verify_stream_token(token)

    external_url = settings.EXTERNAL_URL
    epg_url_str = f"{external_url}/epg.xml"
    if token:
        epg_url_str += f"?token={token}"
    epg_url = HttpUrl(epg_url_str)
    m3u8_header = f'#EXTM3U x-tvg-url="{epg_url}" url-tvg="{epg_url}" refresh="3600"\n'

    ace_lines = get_ace_streams_db_handler().get_iptv_lines(token=token)
    iptv_lines = get_iptv_streams_db_handler().get_iptv_lines(token=token)

    all_lines = sorted(set(ace_lines + iptv_lines))
    m3u8 = m3u8_header + "\n".join(all_lines)

    return Response(
        content=m3u8,
        media_type="application/vnd.apple.mpegurl",
    )
