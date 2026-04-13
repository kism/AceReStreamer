"""Model for persistent content_id to xc_id mapping."""

from sqlmodel import Field, SQLModel


class ContentIdXcId(SQLModel, table=True):
    """Persistent mapping from content_id to XC stream ID. Never deleted."""

    __tablename__ = "content_id_xc_id"
    xc_id: int = Field(primary_key=True)
    content_id: str = Field(max_length=40, unique=True, nullable=False, index=True)
