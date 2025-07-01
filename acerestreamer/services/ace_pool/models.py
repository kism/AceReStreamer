"""Pydantic models for the AcePool service."""

from datetime import datetime, timedelta

from pydantic import BaseModel, field_serializer


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
    ace_id: str
    last_used: datetime
    date_started: datetime
    ace_hls_m3u8_url: str
    ace_stat: AcePoolStat | None

    @field_serializer("time_until_unlock")
    def serialize_time_until_unlock(self, time_until_unlock: timedelta) -> int:
        """Serialize the time until unlock as a timestamp."""
        return time_until_unlock.seconds

    @field_serializer("time_running")
    def serialize_time_running(self, time_running: timedelta) -> int:
        """Serialize the time running as a timestamp."""
        return time_running.seconds


# region AcePool
class AcePoolForApi(BaseModel):
    """Model for the AcePool API response."""

    ace_version: str
    ace_address: str
    max_size: int
    healthy: bool
    transcode_audio: bool
    ace_instances: list[AcePoolEntryForAPI]
