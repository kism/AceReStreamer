"""EPG API Models."""

from datetime import timedelta
from typing import Any

from pydantic import BaseModel, HttpUrl, RootModel, field_serializer


class EPGApiHealthResponse(BaseModel):
    """Model for EPG API response."""

    time_since_last_updated: timedelta
    time_until_next_update: timedelta

    @field_serializer("time_since_last_updated", mode="plain")
    def serialize_time_since_last_updated(self, value: timedelta) -> int:
        """Serialize time since last updated to seconds."""
        return int(value.total_seconds())

    @field_serializer("time_until_next_update", mode="plain")
    def serialize_time_until_next_update(self, value: timedelta) -> int:
        """Serialize time until next update to seconds."""
        return int(value.total_seconds())


class EPGApiHandlerHealthResponse(BaseModel):
    """Model for EPG API handler response."""

    time_until_next_update: timedelta
    tvg_ids: set[str]
    epgs: dict[str, EPGApiHealthResponse]

    @field_serializer("time_until_next_update", mode="plain")
    def serialize_time_until_next_update(self, value: timedelta) -> int:
        """Serialize time until next update to seconds."""
        return int(value.total_seconds())

    @field_serializer("tvg_ids", mode="plain")
    def serialize_tvg_ids(self, value: set[str]) -> list[str]:
        """Serialize TVG IDs to a list."""
        return sorted(value)


class TVGEPGMappingsResponse(RootModel[dict[str, HttpUrl | None]]):
    """Model for TVG EPG mappings response."""

    root: dict[str, HttpUrl | None]

    def model_dump(self, **_: Any) -> dict[str, str | None]:  # noqa: ANN401
        """Serialize mappings with HttpUrl to string."""
        return {tvg_id: str(url) if url else None for tvg_id, url in self.root.items()}
