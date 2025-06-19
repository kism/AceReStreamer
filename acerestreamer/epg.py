"""Module for handling Electronic Program Guide (EPG) data."""

import gzip
import io
from datetime import datetime
from pathlib import Path

import requests
from lxml import etree

from .config import EPGInstanceConf
from .constants import OUR_TIMEZONE
from .logger import get_logger

logger = get_logger(__name__)

EPG_LIFESPAN_SECONDS = 24 * 60 * 60  # 24 hours in seconds


class EPG:
    """An Electronic Program Guide (EPG) entry."""

    def __init__(self, epg_conf: EPGInstanceConf) -> None:
        """Initialize the EPG entry with a URL."""
        self.url = epg_conf.url
        self.format = epg_conf.format
        self._extracted_format = self.format.replace(".gz", "")  # Remove .gz for internal use
        self.region_code = epg_conf.region_code
        self.last_updated = datetime.now(tz=OUR_TIMEZONE)
        self.data: bytes | None = None
        self.saved_file_path: Path | None = None

    def update(self, instance_path: Path) -> None:
        """Update the EPG data from the configured URL."""
        directory_path = instance_path / "epg"
        if not directory_path.is_dir():
            logger.info("Creating EPG directory at %s", directory_path)
            directory_path.mkdir(parents=True, exist_ok=True)

        self.saved_file_path = directory_path / f"{self.region_code}.{self._extracted_format}"
        if not self._time_to_update():
            return

        data_str = self._download_epg()

        self.data = etree.fromstring(data_str)

        self.last_updated = datetime.now(tz=OUR_TIMEZONE)

    def _time_to_update(self) -> bool:
        """Check if the EPG data needs to be updated based on the last update time."""
        if self.last_updated is None:
            if self._check_saved_file_exists():
                # Stat the existing file to get its last modified time
                mtime = self.saved_file_path.stat().st_mtime
                self.last_updated = datetime.fromtimestamp(mtime, tz=OUR_TIMEZONE)
            else:
                return True

        time_since_last_update = (datetime.now(tz=OUR_TIMEZONE) - self.last_updated).total_seconds()
        return time_since_last_update > EPG_LIFESPAN_SECONDS

    def _download_epg(self) -> str:
        """Download the EPG data from the URL."""
        # Placeholder for actual download logic
        logger.info("Downloading EPG data from %s", self.url)
        data: bytes = b""
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            data = response.content

            if self.format == "xml.gz":
                data = self._un_gz_data(data)

            self.last_updated = datetime.now(tz=OUR_TIMEZONE)

        except requests.RequestException as e:
            error_short = type(e).__name__
            logger.error("Failed to download EPG data: %s", error_short)  # noqa: TRY400 Short error is good

        return data.decode("utf-8") if isinstance(data, bytes) else data

    def _un_gz_data(self, data: bytes) -> bytes:
        """Uncompress gzipped EPG data."""
        # Placeholder for actual decompression logic
        logger.info("Uncompressing gzipped EPG data")

        buffer = io.BytesIO(data)
        with gzip.GzipFile(fileobj=buffer, mode="rb") as gz_file:
            return gz_file.read()

    def _check_saved_file_exists(self) -> bool:
        """Check if the saved EPG file exists."""
        return bool(self.saved_file_path and self.saved_file_path.is_file())


class EPGHandler:
    """Handler for EPG (Electronic Program Guide) data."""

    def __init__(self, epg_conf_list: list[EPGInstanceConf], instance_path: Path | None = None) -> None:
        """Initialize the EPGHandler with a list of URLs."""
        self.epgs: list[EPG] = []

        for epg_conf in epg_conf_list:
            self.epgs.append(EPG(epg_conf=epg_conf))

        if instance_path:
            for epg in self.epgs:
                epg.update(instance_path=instance_path)

    def get_epg_names(self) -> list[str]:
        """Get the names of all EPGs."""
        return [epg.region_code for epg in self.epgs]
