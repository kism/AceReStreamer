import random

from pydantic import HttpUrl

from acere.services.ace_pool.models import (
    AceMiddlewareResponse,
    AceMiddlewareResponseFull,
    AcePoolStatResponse,
    AcePoolStatResponseDiskCache,
)


def get_random_content_id() -> str:
    """Generate a 40 digit hex string."""
    return "".join(random.choices("0123456789abcdef", k=40))


def create_mock_middleware_response(
    playback_url: HttpUrl | None = None,
    stat_url: HttpUrl | None = None,
    command_url: HttpUrl | None = None,
    infohash: str | None = None,
    playback_session_id: str = "session123",
) -> AceMiddlewareResponseFull:
    """Create a mock AceMiddlewareResponse for testing."""
    if playback_url is None:
        playback_url = HttpUrl("http://localhost:6878/ace/m/whatever.m3u8")
    if stat_url is None:
        stat_url = HttpUrl("http://localhost:6878/stat/whatever")
    if command_url is None:
        command_url = HttpUrl("http://localhost:6878/ace/cmd/whatever")
    if infohash is None:
        infohash = get_random_content_id()

    mw_info = AceMiddlewareResponse(
        playback_url=playback_url,
        stat_url=stat_url,
        command_url=command_url,
        infohash=infohash,
        playback_session_id=playback_session_id,
        is_live=1,
        is_encrypted=0,
        client_session_id=-1,
    )

    return AceMiddlewareResponseFull(
        response=mw_info,
        error=None,
    )


def create_mock_stat_response(
    playback_session_id: str = "session123",
    infohash: str | None = None,
    status: str = "active",
) -> AcePoolStatResponse:
    """Create a mock AcePoolStatResponse for testing."""
    if infohash is None:
        infohash = get_random_content_id()

    return AcePoolStatResponse(
        uploaded=0,
        network_monitor_status=0,
        debug_level=0,
        disk_cache_stats=AcePoolStatResponseDiskCache(
            avail=0,
            disk_cache_limit=0,
            inactive_inuse=0,
            active_inuse=0,
        ),
        speed_down=0,
        speed_up=0,
        network_monitor_started=False,
        selected_stream_index=0,
        total_progress=0,
        stream_status=0,
        client_session_id=-1,
        status=status,
        downloaded=0,
        manifest_access_mode=0,
        peers=0,
        playback_session_id=playback_session_id,
        is_encrypted=0,
        is_live=1,
        infohash=infohash,
        selected_file_index=0,
    )
