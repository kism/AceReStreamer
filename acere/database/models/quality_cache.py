"""Model for ace content_id quality cache/information."""

from datetime import datetime

from sqlmodel import Field, SQLModel

from acere.database.types import TZDateTime
from acere.services.ace.quality import QUALITY_ON_FIRST_SUCCESS


class AceQualityCache(SQLModel, table=True):
    """Database model for ace content_id quality cache/information."""

    __tablename__ = "ace_quality_cache"
    content_id: str = Field(max_length=40, primary_key=True, unique=True, nullable=False)
    quality: int = Field(nullable=False, default=QUALITY_ON_FIRST_SUCCESS)
    m3u_failures: int = Field(nullable=False, default=0)
    last_quality_success_time: datetime | None = Field(default=None, sa_type=TZDateTime)

    @property
    def has_ever_worked(self) -> bool:
        """Return True if the stream has ever had a successful quality check."""
        return self.last_quality_success_time is not None
