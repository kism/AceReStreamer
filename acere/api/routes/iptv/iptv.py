# """Blueprint for IPTV functionality in Ace Streamer."""

from fastapi import APIRouter, Response

from acere.instances.ace_streams import get_ace_streams_db_handler
from acere.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Media/IPTV"])


@router.get("/iptv", name="iptv_m3u8_1")
@router.get("/iptv.m3u", name="iptv_m3u_2")
@router.get("/iptv.m3u8", name="iptv_m3u8_3")
def iptv() -> Response:
    """Render the IPTV M3U8 Playlist with HLS streams."""
    handler = get_ace_streams_db_handler()
    m3u8 = handler.get_streams_as_iptv(output="hls")

    return Response(
        content=m3u8,
        media_type="application/vnd.apple.mpegurl",
    )


@router.get("/iptv-ts", name="iptv_ts_m3u8_1")
@router.get("/iptv-ts.m3u", name="iptv_ts_m3u_2")
@router.get("/iptv-ts.m3u8", name="iptv_ts_m3u8_3")
def iptv_ts() -> Response:
    """Render the IPTV M3U8 Playlist with MPEG-TS streams."""
    handler = get_ace_streams_db_handler()
    m3u8 = handler.get_streams_as_iptv(output="ts")

    return Response(
        content=m3u8,
        media_type="application/vnd.apple.mpegurl",
    )
