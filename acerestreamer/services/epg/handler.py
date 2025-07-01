"""Module for handling Electronic Program Guide (EPG) data."""

import gzip
import io
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import requests
from lxml import etree

from acerestreamer.utils.constants import OUR_TIMEZONE
from acerestreamer.utils.logger import get_logger

if TYPE_CHECKING:
    from acerestreamer.config import EPGInstanceConf
else:
    EPGInstanceConf = object

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

        self.last_updated = datetime.now(tz=OUR_TIMEZONE)

        if downloaded_file:
            self._write_to_file(data_bytes)  # Write to file after, so empty file is not created if download fails
            logger.info("EPG data for %s updated successfully", self.region_code)

    def get_data(self) -> bytes | None:
        """Get the EPG data as bytes."""
        # I used to have this in RAM, but it got very large with multiple EPGs
        if self.saved_file_path and self.saved_file_path.is_file():
            try:
                return self.saved_file_path.read_bytes()
            except OSError as e:
                error_short = type(e).__name__
                logger.error("%s Failed to read EPG data from %s: %s", error_short, self.saved_file_path, e)  # noqa: TRY400 Fine for this to be a short error
                return None
        else:
            logger.warning("No saved file path defined or file does not exist for EPG %s", self.region_code)
            return None

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
            logger.error("Failed to download EPG data: %s", error_short)  # noqa: TRY400 Short error is good

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


class EPGHandler:
    """Handler for EPG (Electronic Program Guide) data."""

    def __init__(self) -> None:
        """Initialize the EPGHandler with a list of URLs."""
        self.epgs: list[EPG] = []
        self.condensed_epg: etree._Element | None = None
        self.instance_path: Path | None = None
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

    def _create_tv_element(self) -> etree._Element:
        """Create a base XML element for the EPG data."""
        from acerestreamer import PROGRAM_NAME, URL  # noqa: PLC0415 Avoid circular import

        tv_tag = etree.Element("tv")
        tv_tag.set("generator-info-name", PROGRAM_NAME)
        tv_tag.set("generator-info-url", URL)
        return tv_tag

    def merge_epgs(self) -> etree._Element:
        """Merge all EPG data into a single XML structure."""
        logger.info("Merging EPG data from %d sources", len(self.epgs))
        merged_data = self._create_tv_element()  # Create a base XML element for the merged EPG

        for epg in self.epgs:
            epg_data = epg.get_data()
            if epg_data is not None:
                merged_data.extend(
                    etree.fromstring(epg_data)  # Parse the EPG data and extend the merged_data
                )
            else:
                logger.warning("EPG data for %s is None, skipping", epg.region_code)

        return merged_data

    def condense_epgs(self) -> None:
        """Get a condensed version of the merged EPG data."""
        time_since_last_condense: timedelta = datetime.now(tz=OUR_TIMEZONE) - self._last_condense_time
        time_to_update: bool = time_since_last_condense > MIN_TIME_BETWEEN_EPG_PROCESSING

        if self.condensed_epg is not None and not time_to_update:
            return

        merged_epgs = self.merge_epgs()

        if not self.set_of_tvg_ids:
            logger.warning("No TVG IDs found in the current streams, skipping EPG condensation")
            return

        condensed_data = self._create_tv_element()  # Create a base XML element for the merged EPG

        for channel in merged_epgs.findall("channel"):
            tvg_id = channel.get("id")
            if tvg_id in self.set_of_tvg_ids:
                condensed_data.append(channel)

        for programme in merged_epgs.findall("programme"):
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

    def get_condensed_epg(self) -> bytes:
        """Get the condensed EPG data."""
        self.condense_epgs()

        if self.condensed_epg is None:
            logger.error("No condensed EPG data available")
            return b""

        return etree.tostring(self.condensed_epg, encoding="utf-8", xml_declaration=True)

    def get_current_program(self, tvg_id: str) -> tuple[str, str]:
        """Get the current program for a given TVG ID."""
        if self.condensed_epg is None:
            self.condense_epgs()

        if self.condensed_epg is None:
            logger.error("No condensed EPG data available to get current program")
            return "", ""

        # Find the channel with the given TVG ID
        channel = self.condensed_epg.find(f"channel[@id='{tvg_id}']")
        if channel is None:
            return "", ""

        # Find the current programme for this channel
        now = datetime.now(tz=OUR_TIMEZONE)
        programmes = self.condensed_epg.findall(f"programme[@channel='{tvg_id}']")
        for programme in programmes:
            start_time = programme.get("start")
            end_time = programme.get("stop")
            if start_time is None or end_time is None:
                continue

            start_date_time = datetime.strptime(start_time, "%Y%m%d%H%M%S %z")
            end_date_time = datetime.strptime(end_time, "%Y%m%d%H%M%S %z")

            if start_date_time <= now <= end_date_time:
                title_match = programme.find("title")
                program_title = ""
                if title_match is not None:
                    program_title = title_match.text or program_title

                description_match = programme.find("desc")
                program_description = ""
                if description_match is not None:
                    program_description = description_match.text or program_description

                return program_title, program_description

        return "", ""
