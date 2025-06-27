"""Module for handling Electronic Program Guide (EPG) data."""

import gzip
import io
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import requests
from lxml import etree

from acerestreamer.config.models import EPGInstanceConf
from acerestreamer.utils.constants import OUR_TIMEZONE
from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)

EPG_LIFESPAN = timedelta(days=1)
MIN_TIME_BETWEEN_EPG_PROCESSING = timedelta(minutes=20)


class EPG:
    """An Electronic Program Guide (EPG) entry."""

    def __init__(self, epg_conf: EPGInstanceConf) -> None:
        """Initialize the EPG entry with a URL."""
        self.url = epg_conf.url
        self.format = epg_conf.format
        self._extracted_format = self.format.replace(".gz", "")  # Remove .gz for internal use
        self.region_code = epg_conf.region_code
        self.last_updated: datetime | None = None
        self.data: bytes | None = None
        self.saved_file_path: Path | None = None

    def update(self, instance_path: Path) -> None:
        """Update the EPG data from the configured URL."""
        downloaded_file = False
        directory_path = instance_path / "epg"
        if not directory_path.is_dir():
            logger.info("Creating EPG directory at %s", directory_path)
            directory_path.mkdir(parents=True, exist_ok=True)

        self.saved_file_path = directory_path / f"{self.region_code}.{self._extracted_format}"
        if not self._time_to_update():
            logger.info("EPG data for %s is up-to-date, no need to update", self.region_code)
            if self.saved_file_path.is_file():
                data_bytes = self.saved_file_path.read_bytes()
            else:
                logger.error("Entered impossible state: EPG data is not up-to-date but no saved file exists")
        else:
            data_bytes = self._download_epg()
            downloaded_file = True

        self.data = data_bytes
        self.last_updated = datetime.now(tz=OUR_TIMEZONE)

        if downloaded_file:
            self._write_to_file(data_bytes)  # Write to file after, so empty file is not created if download fails
            logger.info("EPG data for %s updated successfully", self.region_code)

    def _time_to_update(self) -> bool:
        """Check if the EPG data needs to be updated based on the last update time."""
        if self.last_updated is None:
            logger.debug("%s: Last updated time is None, will update EPG data", self.region_code)
            if self.saved_file_path is not None and self.saved_file_path.is_file():
                # Stat the existing file to get its last modified time
                mtime = self.saved_file_path.stat().st_mtime
                self.last_updated = datetime.fromtimestamp(mtime, tz=OUR_TIMEZONE)
            else:
                return True

        time_since_last_update = datetime.now(tz=OUR_TIMEZONE) - self.last_updated
        logger.debug("Time since last update for %s: %d seconds", self.region_code, time_since_last_update.seconds)

        return time_since_last_update > EPG_LIFESPAN

    def _download_epg(self) -> bytes:
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

        return data

    def _un_gz_data(self, data: bytes) -> bytes:
        """Uncompress gzipped EPG data."""
        # Placeholder for actual decompression logic
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


class EPGHandler:
    """Handler for EPG (Electronic Program Guide) data."""

    def __init__(self) -> None:
        """Initialize the EPGHandler with a list of URLs."""
        self.epgs: list[EPG] = []
        self.merged_epg: etree._Element | None = None
        self.condensed_epg: etree._Element | None = None
        self.instance_path: Path | None = None
        self._last_merge_time: datetime = datetime.fromtimestamp(0, tz=UTC)  # Arbitrary old time
        self._last_condense_time: datetime = datetime.fromtimestamp(0, tz=UTC)  # Arbitrary old time
        self.set_of_tvg_ids: set[str] = set()

    def load_config(self, epg_conf_list: list[EPGInstanceConf], instance_path: Path | str | None = None) -> None:
        """Load EPG configurations."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)

        self.instance_path = instance_path

        for epg_conf in epg_conf_list:
            self.epgs.append(EPG(epg_conf=epg_conf))

        self.update_epgs()

        logger.info("Initialised EPGHandler with %d EPG configurations", len(epg_conf_list))

    def get_epg_names(self) -> list[str]:
        """Get the names of all EPGs."""
        return [epg.region_code for epg in self.epgs]

    def update_epgs(self) -> None:
        """Update all EPGs with the current instance path."""

        def epg_update_thread() -> None:
            """Thread function to update EPGs."""
            logger.info("Starting EPG update thread")
            while True:
                if self.instance_path is not None:
                    for epg in self.epgs:
                        try:
                            epg.update(instance_path=self.instance_path)
                        except Exception:
                            logger.exception("Failed to update EPG %s", epg.region_code)

                    self.merge_epgs()
                    self.condense_epgs()
                    time.sleep(EPG_LIFESPAN.total_seconds())

                time.sleep(10)  # Sleep to avoid busy waiting

        threading.Thread(target=epg_update_thread, name="EPGHandler: update_epgs", daemon=True).start()

    def merge_epgs(self) -> None:
        """Merge all EPG data into a single XML structure."""
        time_since_last_merge: timedelta = datetime.now(tz=OUR_TIMEZONE) - self._last_merge_time
        time_to_update: bool = time_since_last_merge > MIN_TIME_BETWEEN_EPG_PROCESSING

        if self.merged_epg is not None and not time_to_update:
            return

        logger.info("Merging EPG data from %d sources", len(self.epgs))
        merged_data = etree.Element("tv")

        for epg in self.epgs:
            if epg.data is not None:
                merged_data.extend(
                    etree.fromstring(epg.data)  # Parse the EPG data and extend the merged_data
                )
            else:
                logger.warning("EPG data for %s is None, skipping", epg.region_code)

        self.merged_epg = merged_data
        self._last_merge_time = datetime.now(tz=OUR_TIMEZONE)
        logger.debug("EPG data merged successfully")

    def get_merged_epg(self) -> str:
        """Get the merged EPG data from all configured EPGs."""
        self.merge_epgs()

        if self.merged_epg is None:
            logger.error("No EPG data available to merge")
            return ""

        return etree.tostring(self.merged_epg, encoding="unicode")

    def condense_epgs(self) -> None:
        """Get a condensed version of the merged EPG data."""
        time_since_last_condense: timedelta = datetime.now(tz=OUR_TIMEZONE) - self._last_condense_time
        time_to_update: bool = time_since_last_condense > MIN_TIME_BETWEEN_EPG_PROCESSING

        if self.condensed_epg is not None and not time_to_update:
            return

        if self.merged_epg is None:
            self.merge_epgs()

        if self.merged_epg is None:
            logger.error("No merged EPG data available to condense")
            return

        if not self.set_of_tvg_ids:
            logger.warning("No TVG IDs found in the current streams, skipping EPG condensation")
            return

        condensed_data = etree.Element("tv")
        merged_epg_copy = etree.ElementTree(self.merged_epg)
        for channel in merged_epg_copy.findall("channel"):
            tvg_id = channel.get("id")
            if tvg_id in self.set_of_tvg_ids:
                condensed_data.append(channel)

        for programme in merged_epg_copy.findall("programme"):
            tvg_id = programme.get("channel")
            if tvg_id in self.set_of_tvg_ids:
                condensed_data.append(programme)

        logger.info(
            "Condensed EPG data created with %d channels and %d programmes",
            len(condensed_data.findall("channel")),
            len(condensed_data.findall("programme")),
        )

        self.condensed_epg = condensed_data
        self._last_condense_time = datetime.now(tz=OUR_TIMEZONE)

    def get_condensed_epg(self) -> str:
        """Get the condensed EPG data."""
        logger.warning("get_condensed_epg called, merging and condensing EPG data")
        self.merge_epgs()
        logger.warning("get_condensed_epg called, condensing EPG data")
        self.condense_epgs()

        if self.condensed_epg is None:
            logger.error("No condensed EPG data available")
            return ""

        return etree.tostring(self.condensed_epg, encoding="unicode")
