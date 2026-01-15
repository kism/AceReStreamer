"""EPG API Models."""

from datetime import timedelta

from pydantic import BaseModel, HttpUrl, field_serializer


class EPGApiResponse(BaseModel):
    """Model for EPG API response."""

    url: HttpUrl
    region_code: str
    time_since_last_updated: timedelta
    time_until_next_update: timedelta

    @field_serializer("time_since_last_updated")
    def serialize_time_since_last_updated(self, value: timedelta) -> int:
        """Serialize time since last updated to seconds."""
        return int(value.total_seconds())

    @field_serializer("time_until_next_update")
    def serialize_time_until_next_update(self, value: timedelta) -> int:
        """Serialize time until next update to seconds."""
        return int(value.total_seconds())

    @field_serializer("url")
    def serialize_url(self, value: HttpUrl) -> str:
        """Serialize URL to string."""
        return value.encoded_string()


class EPGApiHandlerResponse(BaseModel):
    """Model for EPG API handler response."""

    time_until_next_update: timedelta
    tvg_ids: set[str]
    epgs: list[EPGApiResponse]

    @field_serializer("time_until_next_update")
    def serialize_time_until_next_update(self, value: timedelta) -> int:
        """Serialize time until next update to seconds."""
        return int(value.total_seconds())

    @field_serializer("tvg_ids")
    def serialize_tvg_ids(self, value: set[str]) -> list[str]:
        """Serialize TVG IDs to a list."""
        return sorted(value)
