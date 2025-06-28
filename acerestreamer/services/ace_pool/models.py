"""Pydantic models for the AcePool service."""

from datetime import datetime, timedelta

from pydantic import BaseModel, field_serializer


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
