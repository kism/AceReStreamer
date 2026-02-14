"""Model for ace content_id quality cache/information."""

from sqlmodel import Field, SQLModel

from acere.services.ace_quality import QUALITY_ON_FIRST_SUCCESS


class AceQualityCache(SQLModel, table=True):
    """Database model for ace content_id quality cache/information."""

    __tablename__ = "ace_quality_cache"
    content_id: str = Field(max_length=40, primary_key=True, unique=True, nullable=False)
    quality: int = Field(nullable=False, default=QUALITY_ON_FIRST_SUCCESS)
    has_ever_worked: bool = Field(nullable=False, default=False)
    m3u_failures: int = Field(nullable=False, default=0)
