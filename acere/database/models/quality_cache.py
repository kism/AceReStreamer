"""Model for stream quality cache/information."""

from datetime import datetime

from sqlmodel import Field, SQLModel

from acere.database.types import TZDateTime
from acere.services.quality import QUALITY_ON_FIRST_SUCCESS


class QualityCache(SQLModel, table=True):
    """Database model for stream quality cache/information."""

    __tablename__ = "quality_cache"
    hls_identifier: str = Field(max_length=2048, primary_key=True, unique=True, nullable=False)
    quality: int = Field(nullable=False, default=QUALITY_ON_FIRST_SUCCESS)
    m3u_failures: int = Field(nullable=False, default=0)
    last_quality_success_time: datetime | None = Field(default=None, sa_type=TZDateTime)

    @property
    def has_ever_worked(self) -> bool:
        """Return True if the stream has ever had a successful quality check."""
        return self.last_quality_success_time is not None
