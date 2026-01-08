"""Pydantic models for the AcePool service."""

from datetime import datetime, timedelta

from pydantic import BaseModel, HttpUrl, field_serializer
from typing_extensions import TypedDict


class AceMiddlewareResponse(BaseModel):
    """Response data from the AceStream middleware."""

    playback_url: HttpUrl
    stat_url: HttpUrl
    command_url: HttpUrl
    infohash: str
    playback_session_id: str
    is_live: int
    is_encrypted: int
    client_session_id: int


class AceMiddlewareResponseFull(BaseModel):
    """Response model for the AceStream middleware https://docs.acestream.net/developers/start-playback/."""

    response: AceMiddlewareResponse | None
    error: str | None


# region Stat
# This is to match the response from the AcePool API for the stat endpoint.
class AcePoolStatResponseDiskCache(BaseModel):
    """Matches the disk cache response from the AcePool API."""

    avail: int
    disk_cache_limit: int
    inactive_inuse: int
    active_inuse: int


class AcePoolStatResponseLivePos(BaseModel):
    """Matches the live position response from the AcePool API."""

    last: int
    live_first: int
    pos: int
    first_ts: int
    last_ts: int
    is_live: int
    live_last: int
    buffer_pieces: int


class AcePoolStatResponse(BaseModel):
    """Matches the response from the AcePool API."""

    # https://docs.acestream.net/developers/start-playback/

    uploaded: int
    network_monitor_status: int
    debug_level: int
    disk_cache_stats: AcePoolStatResponseDiskCache
    speed_down: int
    speed_up: int
    network_monitor_started: bool
    selected_stream_index: int
    total_progress: int
    stream_status: int
    client_session_id: int
    status: str
    downloaded: int
    manifest_access_mode: int
    peers: int
    playback_session_id: str
    is_encrypted: int
    is_live: int
    infohash: str
    selected_file_index: int
    livepos: AcePoolStatResponseLivePos | None = None


class AcePoolStat(BaseModel):
    """Matches the stat response from the AcePool API."""

    # https://docs.acestream.net/developers/start-playback/

    response: AcePoolStatResponse
    error: str | None = None


# region AcePoolEntry
class AcePoolEntryForAPI(BaseModel):
    """Nice model with some calculated fields for the API."""

    locked_in: bool = False
    time_until_unlock: timedelta = timedelta(seconds=0)
    time_running: timedelta = timedelta(seconds=0)
    ace_pid: int
    content_id: str
    last_used: datetime
    date_started: datetime
    ace_hls_m3u8_url: HttpUrl | None = None

    @field_serializer("time_until_unlock")
    def serialize_time_until_unlock(self, time_until_unlock: timedelta) -> int:
        """Serialize the time until unlock as a timestamp."""
        return time_until_unlock.seconds

    @field_serializer("time_running")
    def serialize_time_running(self, time_running: timedelta) -> int:
        """Serialize the time running as a timestamp."""
        return time_running.seconds

    @field_serializer("ace_hls_m3u8_url")
    def serialize_ace_hls_m3u8_url(self, ace_hls_m3u8_url: HttpUrl | None) -> str | None:
        """Serialize the Ace HLS M3U8 URL as a string."""
        return ace_hls_m3u8_url.encoded_string() if ace_hls_m3u8_url else None


# region AcePool
class AcePoolForApi(BaseModel):
    """Model for the AcePool API response."""

    ace_version: str
    ace_address: HttpUrl | None
    max_size: int
    healthy: bool
    transcode_audio: bool
    ace_instances: list[AcePoolEntryForAPI]
    external_url: str

    @field_serializer("ace_address")
    def serialize_ace_address(self, ace_address: HttpUrl | None) -> str | None:
        """Serialize the Ace address as a string."""
        return ace_address.encoded_string() if ace_address else None


class AcePoolAllStatsApi(TypedDict):
    """Model for all stats of AcePool instances."""

    pid: int
    status: AcePoolStat | None
