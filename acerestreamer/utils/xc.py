"""Models for XC API responses."""

from datetime import datetime

from pydantic import BaseModel

from acerestreamer.utils.constants import OUR_TIMEZONE

SAFE_TIMEZONE_NAME = "UTC"
if OUR_TIMEZONE is not None:
    SAFE_TIMEZONE_NAME = OUR_TIMEZONE.tzname(datetime.now(tz=OUR_TIMEZONE)) or "UTC"


class XCUserInfo(BaseModel):
    """Model for XC User Information."""

    username: str = "user"
    password: str = "password"  # noqa: S105
    message: str = "Welcome to AceRestreamer"
    auth: int = 1
    status: str = "Active"
    exp_date: str = "1500000000"
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
    timezone: str = SAFE_TIMEZONE_NAME
    timestamp_now: int = int(datetime.now(tz=OUR_TIMEZONE).timestamp())
    process: bool = True


class XCApiResponse(BaseModel):
    """Model for XC API Response."""

    user_info: XCUserInfo = XCUserInfo()
    server_info: XCServerInfo


class XCCategory(BaseModel):
    """Model for XC Category."""

    category_id: str = "1"
    category_name: str = "All Channels"
    parent_id: str = "0"


class XCStream(BaseModel):
    """Model for XC Stream."""

    num: int = 1
    name: str = "Sample Stream"
    stream_type: str = "live"
    stream_id: str = "1"
    stream_icon: str = ""
    epg_channel_id: str = ""
    added: str = "1500000000"
    is_adult: str = "0"
    category_id: str = "1"
    category_ids: list[str] = ["1"]
    custom_sid: None = None
    tv_archive: str = "0"
    direct_source: str = ""
    tv_archive_duration: str = "0"
