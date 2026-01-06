"""Model for content_id xc_id mapping."""

from sqlmodel import Field, SQLModel


class ContentIdXCID(SQLModel, table=True):
    """Database model for content_id xc_id mapping."""

    __tablename__ = "content_id_xc_id"
    xc_id: int = Field(primary_key=True, nullable=False)
    content_id: str = Field(max_length=40, unique=True, nullable=False)
