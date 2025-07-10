"""Pydantic models for XC (Xtreme Codes) IPTV services."""

from datetime import UTC, datetime
from typing import Self

from pydantic import BaseModel, model_validator

from acerestreamer.utils.constants import OUR_TIMEZONE_NAME
from acerestreamer.utils.logger import get_logger

from .helpers import get_expiry_date

logger = get_logger(__name__)


class XCUserInfo(BaseModel):
    """Model for XC User Information."""

    username: str = "user"
    password: str = "password"  # noqa: S105
    message: str = "Welcome to AceRestreamer"
    auth: int = 1
    status: str = "Active"
    exp_date: str = get_expiry_date()
    is_trial: str = "0"
    active_cons: str = "0"
    created_at: str = "5000000000"
    max_connections: str = "100"
    allowed_output_formats: list[str] = ["m3u8"]


class XCServerInfo(BaseModel):
    """Model for XC Server Information."""

    url: str
    port: int = 80
    https_port: int = 443
    server_protocol: str = "http"
    timezone: str = OUR_TIMEZONE_NAME
    timestamp_now: int = int(datetime.now(tz=UTC).timestamp())  # This is a timestamp
    process: bool = True


class XCApiResponse(BaseModel):
    """Model for XC API Response."""

    user_info: XCUserInfo = XCUserInfo()
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
