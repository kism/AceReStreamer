"""Model for storing ace streams."""

from datetime import UTC, datetime

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class AceStreamDBEntry(SQLModel, table=True):
    """Database model for ace streams."""

    __tablename__ = "ace_streams"
    id: int = Field(primary_key=True, index=True)  # This is also the XC id
    title: str = Field(default="", max_length=255)
    content_id: str = Field(max_length=40, unique=True, nullable=False, index=True)
    infohash: str | None = Field(default=None, max_length=40)
    tvg_id: str = Field(default=None, max_length=100)
    tvg_logo: str | None = Field(default=None, max_length=255)
    group_title: str = Field(default="", max_length=100)
    last_scraped_time: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    @field_validator("last_scraped_time", mode="before")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure last_scraped_time is timezone-aware (SQLite strips tzinfo). NOTE: does not run for ORM loads."""
        if isinstance(v, datetime) and v.tzinfo is None:  # type: ignore[redundant-expr] # ty: ignore[unused-ignore-comment]
            return v.replace(tzinfo=UTC)
        return v
