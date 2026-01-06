"""Pydantic models for XC (Xtream Codes) IPTV services."""

from typing import Self

from pydantic import (
    BaseModel,
    HttpUrl,
    field_serializer,
    field_validator,
    model_validator,
)

from acere.utils.constants import OUR_TIMEZONE_NAME
from acere.utils.logger import get_logger

logger = get_logger(__name__)


class XCUserInfo(BaseModel):
    """Model for XC User Information."""

    username: str
    password: str
    message: str = "Welcome to AceRestreamer"
    auth: int = 1
    status: str = "Active"
    exp_date: str
    is_trial: str = "0"
    active_cons: str = "1"
    created_at: str = "5000000000"
    max_connections: str = "100"
    allowed_output_formats: list[str] = ["m3u8"]


class XCServerInfo(BaseModel):
    """Model for XC Server Information."""

    url: HttpUrl
    port: int
    https_port: int | None
    server_protocol: str
    # rtmp_port would go here, but naa null
    timezone: str = OUR_TIMEZONE_NAME
    timestamp_now: int
    time_now: str
    process: bool = True

    @field_validator("server_protocol", mode="after")
    @classmethod
    def validate_protocol(cls, value: str) -> str:
        """Ensure the server protocol is either http or https."""
        if value not in ["http", "https"]:
            logger.error(
                "Invalid server protocol '%s'. Defaulting to 'http'.",
                value,
            )
            value = "http"
        return value

    @field_serializer("url")
    def serialize_url(self, value: HttpUrl) -> str:
        """Serialize URL to string."""
        return value.encoded_string()


class XCApiResponse(BaseModel):
    """Model for XC API Response."""

    user_info: XCUserInfo
    server_info: XCServerInfo


class XCCategory(BaseModel):
    """Model for XC Category."""

    category_id: str
    category_name: str
    parent_id: int = 0


class XCStream(BaseModel):
    """Model for XC Stream."""

    num: int
    name: str
    stream_type: str = "live"
    stream_id: int
    stream_icon: str
    epg_channel_id: str = ""
    added: str = "1500000000"
    is_adult: str = "0"
    category_id: str
    category_ids: list[str] = []
    custom_sid: None = None
    tv_archive: str = "0"
    direct_source: str = ""
    tv_archive_duration: str = "0"

    @model_validator(mode="after")
    def create_category_ids(self) -> Self:
        """Populate category_ids with category_id."""
        self.category_ids = [self.category_id]
        return self
