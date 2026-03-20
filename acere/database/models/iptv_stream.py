"""Model for storing IPTV proxy streams."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel

from acere.database.types import TZDateTime


class IPTVStreamDBEntry(SQLModel, table=True):
    """Database model for IPTV proxy streams."""

    __tablename__ = "iptv_streams"
    id: int | None = Field(default=None, primary_key=True, index=True)
    title: str = Field(default="", max_length=255)
    upstream_url: str = Field(max_length=2048, nullable=False)
    slug: str = Field(max_length=16, unique=True, nullable=False, index=True)
    source_name: str = Field(max_length=255, nullable=False)
    tvg_id: str = Field(default="", max_length=100)
    tvg_logo: str | None = Field(default=None, max_length=255)
    group_title: str = Field(default="", max_length=100)
    last_scraped_time: datetime = Field(default_factory=lambda: datetime.now(tz=UTC), sa_type=TZDateTime)
