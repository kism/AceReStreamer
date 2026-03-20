"""Model for XC stream mapping."""

from sqlmodel import Field, SQLModel


class XCStreamMap(SQLModel, table=True):
    """Maps a unified XC ID to a stream_type + stream_key pair.

    stream_type: "ace" or "iptv"
    stream_key: content_id (for ace) or slug (for iptv)
    """

    __tablename__ = "xc_stream_map"
    xc_id: int | None = Field(default=None, primary_key=True, index=True)
    stream_type: str = Field(max_length=10, nullable=False)
    stream_key: str = Field(max_length=64, nullable=False)
