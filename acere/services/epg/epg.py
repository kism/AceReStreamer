"""Individual EPG Object."""

import gzip
import io
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import aiohttp
from lxml import etree

from acere.constants import EPG_XML_DIR, OUR_TIMEZONE
from acere.core.config import EPGInstanceConf
from acere.utils.exception_handling import log_aiohttp_exception
from acere.utils.helpers import slugify
from acere.utils.logger import get_logger

from .helpers import normalise_epg_tvg_id

if TYPE_CHECKING:
    from pathlib import Path

    from acere.core.config import EPGInstanceConf
else:
    Path = object
    EPGInstanceConf = object

logger = get_logger(__name__)

EPG_LIFESPAN = timedelta(hours=6)
ONE_WEEK = timedelta(days=7)


class EPG:
    """An Electronic Program Guide (EPG) entry."""

    def __init__(self, epg_conf: EPGInstanceConf) -> None:
        """Initialize the EPG entry with a URL."""
        self.url = epg_conf.url
        self.format = epg_conf.format
        self._extracted_format = self.format.replace(".gz", "")  # Remove .gz for internal use
        self._overrides = epg_conf.tvg_id_overrides
        self.region_code = epg_conf.region_code
        self.last_updated: datetime | None = None
        self.saved_file_path: Path | None = None

    async def update(self) -> bool:
        """Update the EPG data from the configured URL, returns true if updated with new data."""
        if not EPG_XML_DIR.is_dir():
            logger.info("Creating EPG directory at %s", EPG_XML_DIR)
            EPG_XML_DIR.mkdir(parents=True, exist_ok=True)

        file_name = f"{self.region_code}-{slugify(self.url.host) + slugify(self.url.path)}.{self._extracted_format}"
        self.saved_file_path = EPG_XML_DIR / file_name

        if self._time_to_update():
            data_bytes = await self._download_epg()

            if data_bytes:
                self._write_to_file(data_bytes)
                logger.info("EPG data for %s/%s updated successfully", self.region_code, self.url)
                return True

            logger.error("Failed to download EPG data for %s", self.region_code)

        return False

    # region Getters
    def _get_data(self) -> bytes | None:
        """Get the EPG data as bytes."""
        # I used to have this in RAM, but it got very large with multiple EPGs

        if self.saved_file_path and self.saved_file_path.is_file():
            if self.saved_file_path.stat().st_size == 0:
                logger.warning("EPG file %s is empty, removing.", self.saved_file_path)
                self.saved_file_path.unlink()
                return None

            try:
                return self.saved_file_path.read_bytes()
            except OSError as e:
                error_short = type(e).__name__
                logger.error(
                    "%s Failed to read EPG data from %s: %s",
                    error_short,
                    self.saved_file_path,
                    e,
                )
                return None
        else:
            logger.warning(
                "No saved file path defined or file does not exist for EPG %s, %s ", self.region_code, self.url
            )
            return None

    def get_epg_etree_normalised(self) -> etree._Element | None:
        epg_data = self._get_data()
        if epg_data is None:
            logger.warning("EPG data for %s is None, skipping", self.region_code)
            return None

        try:
            wip_etree = etree.fromstring(epg_data)
        except etree.XMLSyntaxError:
            logger.error("Failed to parse EPG XML data for %s", self.region_code)
            return None

        for channel in wip_etree.findall("channel"):
            tvg_id = normalise_epg_tvg_id(channel.get("id"), self._overrides)
            if tvg_id:
                channel.set("id", tvg_id)

        for programme in wip_etree.findall("programme"):
            tvg_id = normalise_epg_tvg_id(programme.get("channel"), self._overrides)
            if tvg_id:
                programme.set("channel", tvg_id)

        return wip_etree

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

    async def _download_epg(self) -> bytes:
        """Download the EPG data from the URL."""
        logger.info("Downloading EPG data from %s", self.url)
        data: bytes = b""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url.encoded_string()) as response:
                    response.raise_for_status()
                    data = await response.read()

            if self.format == "xml.gz":
                data = self._un_gz_data(data)

            self.last_updated = datetime.now(tz=OUR_TIMEZONE)

        except aiohttp.ClientError as e:
            log_aiohttp_exception(logger, self.url, e)

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
