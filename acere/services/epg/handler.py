"""Module for handling Electronic Program Guide (EPG) data."""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from lxml import etree

from acere.constants import OUR_TIMEZONE
from acere.utils.logger import get_logger
from acere.version import PROGRAM_NAME, URL

from .candidate import EPGCandidateHandler
from .epg import EPG, EPG_LIFESPAN
from .helpers import find_current_program_xml
from .models import EPGApiHandlerResponse, EPGApiResponse

if TYPE_CHECKING:
    from acere.core.config import EPGInstanceConf
else:
    EPGInstanceConf = object

logger = get_logger(__name__)

EPG_CHECK_INTERVAL_MINIMUM = timedelta(minutes=1)  # Used if EPG is incomplete


class EPGHandler:
    """Handler for EPG (Electronic Program Guide) data."""

    def __init__(self) -> None:
        """Initialize the EPGHandler with a list of URLs."""
        self.epgs: list[EPG] = []
        self.condensed_epg: etree._Element | None = None
        self.condensed_epg_bytes: bytes = b""
        self.instance_path: Path | None = None
        self.set_of_tvg_ids: set[str] = set()  # Desired TVG IDs to include in condensed EPG
        self.next_update_time: datetime = datetime.now(tz=OUR_TIMEZONE)
        self._update_threads: list[threading.Thread] = []

    def load_config(
        self,
        epg_conf_list: list[EPGInstanceConf],
        instance_path: Path | str | None = None,
    ) -> None:
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
    def _populate_candidate_handler(self) -> EPGCandidateHandler:
        """Populate the EPGCandidateHandler with data from all EPGs."""
        candidate_handler = EPGCandidateHandler()

        for epg in self.epgs:
            epg_etree = epg.get_epg_etree_normalised()
            if epg_etree is None:
                continue  # Error message is elsewhere

            for channel in epg_etree.findall("channel"):
                tvg_id = channel.get("id")
                if tvg_id in self.set_of_tvg_ids:
                    candidate_handler.add_channel(tvg_id, epg.url, channel)

            for programme in epg_etree.findall("programme"):
                tvg_id = programme.get("channel")
                if tvg_id in self.set_of_tvg_ids:
                    candidate_handler.add_program(tvg_id, epg.url, programme)

        return candidate_handler

    def _condense_epgs(self) -> None:
        """Get a condensed version of the merged EPG data."""
        if not self.set_of_tvg_ids:
            logger.warning("No TVG IDs found in the current streams, skipping EPG condensation")
            return

        candidate_handler = self._populate_candidate_handler()
        if candidate_handler.get_number_of_candidates() == 0:
            logger.warning("No EPG candidates found, skipping EPG condensation")
            return

        new_condensed_data = self._create_tv_element()

        for tvg_id in self.set_of_tvg_ids:
            candidate = candidate_handler.get_best_candidate(tvg_id)
            if candidate is None:
                logger.debug("No candidate found for TVG ID %s", tvg_id)
                continue

            new_condensed_data.extend(candidate.get_channels_programs())

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
            if tvg_id != "":
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

        return find_current_program_xml(tvg_id, self.condensed_epg)

    # region API
    def get_epgs_api(self) -> EPGApiHandlerResponse:
        """Get the names of all EPGs."""
        epgs = [
            EPGApiResponse(
                url=epg.url,
                region_code=epg.region_code,
                time_since_last_updated=epg.get_time_since_last_update(),
                time_until_next_update=epg.get_time_until_next_update(),
            )
            for epg in self.epgs
        ]

        time_until_next_update = self.next_update_time - datetime.now(tz=OUR_TIMEZONE)
        return EPGApiHandlerResponse(
            time_until_next_update=time_until_next_update,
            tvg_ids=self.set_of_tvg_ids,
            epgs=epgs,
        )

    # region Update Thread
    def _get_time_to_next_update(self) -> timedelta:
        """Get the time until the next EPG update."""
        wait_time = EPG_LIFESPAN

        if self.instance_path is None:
            logger.error("Instance path is not set, cannot get time to next update")
            return EPG_CHECK_INTERVAL_MINIMUM

        for epg in self.epgs:
            if epg.last_updated is None:
                return EPG_CHECK_INTERVAL_MINIMUM

            wait_time = min(wait_time, epg.get_time_until_next_update())

        # Don't remove the additional wait time, i'm scared of a race condition
        time_to_wait = min(wait_time + EPG_CHECK_INTERVAL_MINIMUM, EPG_LIFESPAN)

        logger.info(
            "Next EPG update in %s",
            str(time_to_wait).split(".")[0],  # Remove microseconds
        )

        return time_to_wait

    def _update_epgs(self) -> None:  # noqa: C901 I split it up within the function
        """Update all EPGs with the current instance path."""
        if self.instance_path is None:
            logger.error("Instance path is not set, cannot update EPGs")
            return

        async def _safe_update_epg(epg: EPG) -> bool:
            """Safely update a single EPG with exception handling."""
            try:
                return await epg.update()
            except Exception:
                logger.exception("Failed to update EPG %s", epg.region_code)
                return False

        async def _update_epgs_async() -> bool:
            """Asynchronous function to update EPGs."""
            any_epg_updated = False
            tasks = [_safe_update_epg(epg) for epg in self.epgs]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.exception("Failed to update EPG %s: %s", self.epgs[i].region_code, result)
                elif result:
                    any_epg_updated = True

            return any_epg_updated

        def epg_update_thread() -> None:
            """Thread function to update EPGs."""
            logger.info("Starting EPG update thread")
            while True:
                epg_actually_updated = asyncio.run(_update_epgs_async())

                if epg_actually_updated:
                    time.sleep(10)  # Bit silly but prevents double condense on startup
                    try:
                        logger.info("There are epg updates, condensing EPGs now.")
                        self._condense_epgs()
                    except Exception:
                        logger.exception("Failed to condense EPGs")

                time_until_next_update = self._get_time_to_next_update()
                self.next_update_time = datetime.now(tz=OUR_TIMEZONE) + time_until_next_update

                time.sleep(time_until_next_update.total_seconds())

        for thread in self._update_threads:
            if thread.is_alive():
                thread.join(timeout=1)

        thread = threading.Thread(target=epg_update_thread, name="EPGHandler: _update_epgs", daemon=True)
        thread.start()
        self._update_threads.append(thread)
