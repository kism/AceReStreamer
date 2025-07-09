"""Module for handling Electronic Program Guide (EPG) data."""

import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from lxml import etree

from acerestreamer.utils.constants import OUR_TIMEZONE
from acerestreamer.utils.logger import get_logger
from acerestreamer.version import PROGRAM_NAME, URL

from .epg import EPG
from .models import EPGApiResponse

if TYPE_CHECKING:
    from acerestreamer.config import EPGInstanceConf
else:
    EPGInstanceConf = object

logger = get_logger(__name__)

EPG_CHECK_INTERVAL = timedelta(hours=1)
EPG_CHECK_INTERVAL_MINIMUM = timedelta(minutes=1)  # Used if EPG is incomplete


class EPGHandler:
    """Handler for EPG (Electronic Program Guide) data."""

    def __init__(self) -> None:
        """Initialize the EPGHandler with a list of URLs."""
        self.epgs: list[EPG] = []
        self.condensed_epg: etree._Element | None = None
        self.condensed_epg_bytes: bytes = b""
        self.instance_path: Path | None = None
        self.set_of_tvg_ids: set[str] = set()

    def load_config(self, epg_conf_list: list[EPGInstanceConf], instance_path: Path | str | None = None) -> None:
        """Load EPG configurations."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)

        self.instance_path = instance_path

        for epg_conf in epg_conf_list:
            self.epgs.append(EPG(epg_conf=epg_conf))

        self._update_epgs()

        logger.info("Initialised EPGHandler with %d EPG configurations", len(epg_conf_list))

    # region Helpers
    def _create_tv_element(self) -> etree._Element:
        """Create a base XML element for the EPG data."""
        tv_tag = etree.Element("tv")
        tv_tag.set("generator-info-name", PROGRAM_NAME)
        tv_tag.set("generator-info-url", URL)
        return tv_tag

    # region Condense & Merge
    def _merge_epgs(self) -> etree._Element:
        """Merge all EPG data into a single XML structure."""
        logger.debug("Merging EPG data from %d sources", len(self.epgs))
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

    def _condense_epgs(self) -> None:
        """Get a condensed version of the merged EPG data."""
        merged_epgs = self._merge_epgs()

        if not self.set_of_tvg_ids:
            logger.warning("No TVG IDs found in the current streams, skipping EPG condensation")
            return

        new_condensed_data = self._create_tv_element()  # Create a base XML element for the merged EPG

        for channel in merged_epgs.findall("channel"):
            tvg_id = channel.get("id")
            if tvg_id in self.set_of_tvg_ids:
                new_condensed_data.append(channel)

        for programme in merged_epgs.findall("programme"):
            tvg_id = programme.get("channel")
            if tvg_id in self.set_of_tvg_ids:
                new_condensed_data.append(programme)

        logger.info(
            "Condensed EPG data created with %d channels and %d programmes",
            len(new_condensed_data.findall("channel")),
            len(new_condensed_data.findall("programme")),
        )

        # Update EPG ET, generate bytes local
        self.condensed_epg = new_condensed_data
        new_condensed_epg_bytes = etree.tostring(self.condensed_epg, encoding="utf-8", xml_declaration=True)

        # Check bytes, local vs self.
        if new_condensed_epg_bytes == self.condensed_epg_bytes:
            logger.warning("Condensed EPG data is the same as before")

        # Update the condensed EPG bytes
        self.condensed_epg_bytes = new_condensed_epg_bytes

    # region Setters
    def add_tvg_ids(self, tvg_ids: list[str]) -> None:
        """Set the TVG IDs for which EPG data should be condensed."""
        for tvg_id in tvg_ids:
            self.set_of_tvg_ids.add(tvg_id)

        # This needs to be forced, otherwise the list might be empty on startup
        self._condense_epgs()

    # region Getters
    def get_condensed_epg(self) -> bytes:
        """Get the condensed EPG data."""
        return self.condensed_epg_bytes

    def get_current_program(self, tvg_id: str) -> tuple[str, str]:
        """Get the current program for a given TVG ID."""
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

    # region API
    def get_epgs_api(self) -> list[EPGApiResponse]:
        """Get the names of all EPGs."""
        response = []
        for epg in self.epgs:
            seconds_since_last_updated = epg.get_seconds_since_last_update()
            seconds_until_next_update = epg.get_seconds_until_next_update()
            response.append(
                EPGApiResponse(
                    url=epg.url,
                    region_code=epg.region_code,
                    seconds_since_last_updated=seconds_since_last_updated,
                    seconds_until_next_update=seconds_until_next_update,
                )
            )
        return response

    # region Update Thread
    def _get_time_to_next_update(self) -> timedelta:
        """Get the time until the next EPG update."""
        wait_time = EPG_CHECK_INTERVAL

        if self.instance_path is None:
            logger.error("Instance path is not set, cannot get time to next update")
            return EPG_CHECK_INTERVAL_MINIMUM

        current_time = datetime.now(tz=OUR_TIMEZONE)

        for epg in self.epgs:
            if epg.last_updated is None:
                return EPG_CHECK_INTERVAL_MINIMUM

            time_delta_since_update = current_time - epg.last_updated

            wait_time = min(wait_time, time_delta_since_update)

        # Don't remove the additional wait time, i'm scared of a race condition
        time_to_wait = min(wait_time + EPG_CHECK_INTERVAL_MINIMUM, EPG_CHECK_INTERVAL)

        logger.info(
            "Next EPG update in %s",
            str(time_to_wait).split(".")[0],  # Remove microseconds
        )

        return time_to_wait

    def _update_epgs(self) -> None:
        """Update all EPGs with the current instance path."""
        if self.instance_path is None:
            logger.error("Instance path is not set, cannot update EPGs")
            return

        def epg_update_thread() -> None:
            """Thread function to update EPGs."""
            logger.info("Starting EPG update thread")
            while True:
                epg_actually_updated = False
                for epg in self.epgs:
                    try:
                        if epg.update(instance_path=self.instance_path):
                            epg_actually_updated = True
                    except Exception:
                        logger.exception("Failed to update EPG %s", epg.region_code)

                if epg_actually_updated:
                    time.sleep(3)  # Bit silly but prevents double condense on startup
                    try:
                        self._condense_epgs()
                    except Exception:
                        logger.exception("Failed to condense EPGs")

                time.sleep(self._get_time_to_next_update().total_seconds())

        threading.Thread(target=epg_update_thread, name="EPGHandler: _update_epgs", daemon=True).start()
