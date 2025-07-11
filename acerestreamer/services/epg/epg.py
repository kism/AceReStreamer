"""Individual EPG Object."""

import gzip
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import requests

from acerestreamer.utils.constants import OUR_TIMEZONE
from acerestreamer.utils.logger import get_logger

if TYPE_CHECKING:
    from acerestreamer.config import EPGInstanceConf
else:
    EPGInstanceConf = object

logger = get_logger(__name__)

EPG_LIFESPAN = timedelta(days=1)
ONE_WEEK = timedelta(days=7)


class EPG:
    """An Electronic Program Guide (EPG) entry."""

    def __init__(self, epg_conf: EPGInstanceConf) -> None:
        """Initialize the EPG entry with a URL."""
        self.url = epg_conf.url
        self.format = epg_conf.format
        self._extracted_format = self.format.replace(".gz", "")  # Remove .gz for internal use
        self.region_code = epg_conf.region_code
        self.last_updated: datetime | None = None
        self.saved_file_path: Path | None = None

    def update(self, instance_path: Path | None) -> bool:
        """Update the EPG data from the configured URL."""
        if instance_path is None:
            logger.error("Instance path is not set, cannot update EPG %s", self.region_code)
            return False

        directory_path = instance_path / "epg"
        if not directory_path.is_dir():
            logger.info("Creating EPG directory at %s", directory_path)
            directory_path.mkdir(parents=True, exist_ok=True)

        self.saved_file_path = directory_path / f"{self.region_code}.{self._extracted_format}"

        if self._time_to_update():
            data_bytes = self._download_epg()

            if data_bytes:
                self._write_to_file(data_bytes)
                logger.info("EPG data for %s updated successfully", self.region_code)
                return True

            logger.error("Failed to download EPG data for %s", self.region_code)
            return False

        return False

    # region Getters
    def get_data(self) -> bytes | None:
        """Get the EPG data as bytes."""
        # I used to have this in RAM, but it got very large with multiple EPGs
        if self.saved_file_path and self.saved_file_path.is_file():
            try:
                return self.saved_file_path.read_bytes()
            except OSError as e:
                error_short = type(e).__name__
                logger.error("%s Failed to read EPG data from %s: %s", error_short, self.saved_file_path, e)  # noqa: TRY400 Short error for requests
                return None
        else:
            logger.warning("No saved file path defined or file does not exist for EPG %s", self.region_code)
            return None

    def get_time_since_last_update(self) -> timedelta:
        """Get the time since the EPG was last updated."""
        if self.last_updated is None:
            return ONE_WEEK

        current_time = datetime.now(tz=OUR_TIMEZONE)
        return current_time - self.last_updated

    def get_time_until_next_update(self) -> timedelta:
        """Get the time until the next EPG update."""
        min_timedelta = timedelta(seconds=0)
        if self.last_updated is None:
            return min_timedelta

        time_since_last_update = datetime.now(tz=OUR_TIMEZONE) - self.last_updated
        time_until_next_update = EPG_LIFESPAN - time_since_last_update
        return max(min_timedelta, time_until_next_update)

    # region Helpers
    def _time_to_update(self) -> bool:
        """Check if the EPG data needs to be updated based on the last update time."""
        if self.last_updated is None:  # If we havent updated this EPG
            if self.saved_file_path is not None and self.saved_file_path.is_file():
                # Stat the existing file to get its last modified time, this is the last updated time
                mtime = self.saved_file_path.stat().st_mtime
                self.last_updated = datetime.fromtimestamp(mtime, tz=OUR_TIMEZONE)
            else:
                return True  # If no file exists, we need to update

        time_since_last_update = datetime.now(tz=OUR_TIMEZONE) - self.last_updated
        need_to_update = time_since_last_update > EPG_LIFESPAN

        logger.debug(
            "Time since last update for %s: %s, lifespan: %s, need_to_update=%s",
            self.region_code,
            time_since_last_update,
            EPG_LIFESPAN,
            need_to_update,
        )

        return need_to_update

    def _download_epg(self) -> bytes:
        """Download the EPG data from the URL."""
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
            logger.error("Failed to download EPG data: %s", error_short)  # noqa: TRY400 Short error for requests

        return data

    def _un_gz_data(self, data: bytes) -> bytes:
        """Uncompress gzipped EPG data."""
        logger.info("Uncompressing gzipped EPG data")

        buffer = io.BytesIO(data)
        with gzip.GzipFile(fileobj=buffer, mode="rb") as gz_file:
            return gz_file.read()

    def _write_to_file(self, data: bytes) -> None:
        """Write the EPG data to a file."""
        if self.saved_file_path:
            logger.info("Writing EPG data to %s", self.saved_file_path)
            with self.saved_file_path.open("wb") as file:
                file.write(data)
        else:
            logger.error("No saved file path defined for EPG data")
