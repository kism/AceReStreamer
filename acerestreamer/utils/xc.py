"""Models for XC API responses."""

import csv
from datetime import UTC, datetime
from pathlib import Path

from bidict import bidict
from pydantic import BaseModel

from acerestreamer.utils.constants import OUR_TIMEZONE_NAME


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
    timezone: str = OUR_TIMEZONE_NAME
    timestamp_now: int = int(datetime.now(tz=UTC).timestamp())  # This is a timestamp
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

    num: int
    name: str
    stream_type: str = "live"
    stream_id: int
    stream_icon: str
    epg_channel_id: str = ""
    added: str = "1500000000"
    is_adult: str = "0"
    category_id: str = "1"
    category_ids: list[str] = ["1"]
    custom_sid: None = None
    tv_archive: str = "0"
    direct_source: str = ""
    tv_archive_duration: str = "0"


class ContentIDXCIdMapping:
    """A class to manage the mapping between content IDs and xc stream ids."""

    def __init__(self) -> None:
        """Initialize the mapping."""
        self.content_id_xc_id_mapping: bidict[str, int] = bidict()
        self.config_path: Path | None = None
        self.ace_url: str | None = None

    def load_config(self, instance_path: str | Path) -> None:
        """Load the content ID to xc stream id mapping from a csv file."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)
        self.config_path = instance_path / "content_id_xc_id_map.csv"

        if not self.config_path.exists():
            return

        with self.config_path.open("r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:  # noqa: PLR2004
                    content_id, xc_id = row
                    self.content_id_xc_id_mapping[content_id] = int(xc_id)

    def save_config(self) -> None:
        """Save the content ID to infohash mapping to a JSON file."""
        if self.config_path is None:
            logger.error("Instance path is not set. Cannot save configuration.")
            return

        with self.config_path.open("w", encoding="utf-8") as file:
            writer = csv.writer(file)
            for content_id, infohash in self.content_id_xc_id_mapping.items():
                writer.writerow([content_id, infohash])

    def _get_next_xc_id(self) -> int:
        """Get the next available xc stream id."""
        if not self.content_id_xc_id_mapping:
            return 1
        return max(self.content_id_xc_id_mapping.values()) + 1

    def get_xc_id(self, content_id: str) -> int:
        """Get the xc stream id for a given content ID."""
        if content_id in self.content_id_xc_id_mapping:
            return self.content_id_xc_id_mapping[content_id]

        # If the content ID is not found, create a new xc stream id
        new_xc_id = self._get_next_xc_id()
        self.content_id_xc_id_mapping[content_id] = new_xc_id
        self.save_config()
        return new_xc_id

    def get_content_id(self, xc_id: int) -> str | None:
        """Get the content ID for a given xc stream id."""
        try:
            return self.content_id_xc_id_mapping.inverse[xc_id]
        except KeyError:
            return None


content_id_xc_id_mapping: ContentIDXCIdMapping = ContentIDXCIdMapping()
