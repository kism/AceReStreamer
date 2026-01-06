"""Model for content_id infohash mapping."""

from sqlmodel import Field, SQLModel


class ContentIdInfohash(SQLModel, table=True):
    """Database model for content_id infohash mapping."""

    id: int = Field(primary_key=True)
    content_id: str = Field(max_length=40, unique=True, nullable=False)
    infohash: str = Field(max_length=40, unique=True, nullable=False)
