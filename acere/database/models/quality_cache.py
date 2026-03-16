"""Model for ace content_id quality cache/information."""

from datetime import UTC, datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from acere.services.ace_quality import QUALITY_ON_FIRST_SUCCESS


class AceQualityCache(SQLModel, table=True):
    """Database model for ace content_id quality cache/information."""

    __tablename__ = "ace_quality_cache"
    content_id: str = Field(max_length=40, primary_key=True, unique=True, nullable=False)
    quality: int = Field(nullable=False, default=QUALITY_ON_FIRST_SUCCESS)
    m3u_failures: int = Field(nullable=False, default=0)
    last_quality_success_time: datetime | None = Field(default=None)

    @field_validator("last_quality_success_time", mode="before")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime | None) -> datetime | None:
        """Ensure last_quality_success_time is timezone-aware (SQLite strips tzinfo)."""
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v

    @property
    def has_ever_worked(self) -> bool:
        """Return True if the stream has ever had a successful quality check."""
        return self.last_quality_success_time is not None
