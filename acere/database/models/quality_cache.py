"""Model for ace content_id quality cache/information."""

from sqlmodel import Field, SQLModel


class AceQualityCache(SQLModel, table=True):
    """Database model for ace content_id quality cache/information."""

    content_id: str = Field(max_length=40, primary_key=True, unique=True, nullable=False)
    quality: int = Field(nullable=False)
    has_ever_worked: bool = Field(nullable=False, default=False)
    m3u_failures: int = Field(nullable=False, default=0)
