"""Module for handling Electronic Program Guide (EPG) data."""

import asyncio
import threading
import urllib.parse
from datetime import UTC, datetime, timedelta
from io import BytesIO
from typing import TYPE_CHECKING

from lxml import etree

from acere.utils.helpers import slugify
from acere.utils.logger import get_logger
from acere.version import PROGRAM_NAME, URL

from .candidate import EPGCandidateHandler
from .epg import EPG, EPG_LIFESPAN
from .helpers import find_current_program_xml
from .models import EPGApiHandlerHealthResponse, EPGApiHealthResponse, TVGEPGMappingsResponse

if TYPE_CHECKING:
    from pydantic import HttpUrl

    from acere.core.config import EPGInstanceConf
else:
    EPGInstanceConf = object
    HttpUrl = object

logger = get_logger(__name__)

EPG_CHECK_INTERVAL_MINIMUM = timedelta(minutes=1)  # Used if EPG is incomplete


class EPGHandler:
    """Handler for EPG (Electronic Program Guide) data."""

    def __init__(self, instance_id: str) -> None:
        """Initialize the EPGHandler with a list of URLs."""
        self._instance_id = instance_id
        self._epgs: list[EPG] = []
        self._condensed_epg: etree._Element | None = None
        self._condensed_epg_bytes: bytes = b""
        self._set_of_tvg_ids: set[str] = set()  # Desired TVG IDs to include in condensed EPG
        self._tvg_epg_mappings: dict[str, HttpUrl | None] = {}
        self._next_update_time: datetime = datetime.now(tz=UTC)
        self._threads: list[threading.Thread] = []
        self._stop_event = threading.Event()
        self._last_warned_current_program: datetime = datetime.min.replace(tzinfo=UTC)

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

        for epg in self._epgs:
            # Use streaming parser to avoid loading entire tree into memory
            epg_data = epg.get_data()
            if epg_data is None:
                continue

            try:
                # Parse incrementally, only keeping elements we need
                context = etree.iterparse(
                    BytesIO(epg_data),
                    events=("end",),
                    tag=("channel", "programme"),
                )

                for _event, elem in context:
                    if elem.tag == "channel":
                        tvg_id = epg.normalize_tvg_id(elem.get("id"))
                        if tvg_id and tvg_id in self._set_of_tvg_ids:
                            elem.set("id", tvg_id)
                            candidate_handler.add_channel(tvg_id, epg.url, elem)
                    elif elem.tag == "programme":
                        tvg_id = epg.normalize_tvg_id(elem.get("channel"))
                        if tvg_id and tvg_id in self._set_of_tvg_ids:
                            elem.set("channel", tvg_id)
                            candidate_handler.add_program(tvg_id, epg.url, elem)

                    # Clear element after processing to free memory
                    elem.clear()
                    # Also clear preceding siblings
                    while elem.getprevious() is not None:
                        del elem.getparent()[0]

                del context
            except etree.XMLSyntaxError:
                logger.error("Failed to parse EPG XML data for %s", epg.url)
                continue

        return candidate_handler

    def _condense_epgs(self) -> None:
        """Get a condensed version of the merged EPG data."""
        if not self._set_of_tvg_ids:
            logger.warning("No TVG IDs found in the current streams, skipping EPG condensation")
            return

        candidate_handler = self._populate_candidate_handler()
        if candidate_handler.get_number_of_candidates() == 0:
            logger.warning("No EPG candidates found, skipping EPG condensation")
            return

        new_condensed_data = self._create_tv_element()

        for tvg_id in self._set_of_tvg_ids:
            candidate = candidate_handler.get_best_candidate(tvg_id)
            if candidate is None:
                logger.debug("No candidate found for TVG ID %s", tvg_id)
                self._tvg_epg_mappings[tvg_id] = None
                continue

            self._tvg_epg_mappings[tvg_id] = candidate.epg_url
            new_condensed_data.extend(candidate.get_channels_programs())

        logger.info(
            "Condensed EPG data created with %d channels and %d programmes",
            len(new_condensed_data.findall("channel")),
            len(new_condensed_data.findall("programme")),
        )

        # Update EPG ET, generate bytes local
        self._condensed_epg = new_condensed_data
        new_condensed_epg_bytes = etree.tostring(self._condensed_epg, encoding="utf-8", xml_declaration=True)

        # Check bytes, local vs self.
        if new_condensed_epg_bytes == self._condensed_epg_bytes:
            logger.debug("Condensed EPG data is the same as before")

        # Update the condensed EPG bytes
        self._condensed_epg_bytes = new_condensed_epg_bytes

    # region Setters
    def add_tvg_ids(self, tvg_ids: list[str]) -> None:
        """Set the TVG IDs for which EPG data should be condensed."""
        for tvg_id in tvg_ids:
            if tvg_id != "":
                self._set_of_tvg_ids.add(tvg_id)

        logger.critical("Adding TVG IDs: %s", tvg_ids)

        # This needs to be forced, otherwise the list might be empty on startup
        self._condense_epgs()

    # region Getters
    def get_condensed_epg(self) -> bytes:
        """Get the condensed EPG data."""
        return self._condensed_epg_bytes

    def get_current_program(self, tvg_id: str) -> tuple[str, str]:
        """Get the current program for a given TVG ID."""
        if len(self._epgs) == 0:
            if datetime.now(tz=UTC) - self._last_warned_current_program > EPG_CHECK_INTERVAL_MINIMUM:
                logger.warning(
                    "No EPGs loaded, cannot get program for TVG_ID %s",
                    tvg_id,
                )
                self._last_warned_current_program = datetime.now(tz=UTC)
            return "", ""
        if self._condensed_epg is None:
            if datetime.now(tz=UTC) - self._last_warned_current_program > EPG_CHECK_INTERVAL_MINIMUM:
                logger.warning(
                    "No condensed EPG data loaded, cannot get program for TVG_ID %s",
                    tvg_id,
                )
                self._last_warned_current_program = datetime.now(tz=UTC)

            return "", ""

        return find_current_program_xml(tvg_id, self._condensed_epg)

    # region API
    def get_epgs_api(self) -> EPGApiHandlerHealthResponse:
        """Get the names of all EPGs."""
        epgs: dict[str, EPGApiHealthResponse] = {
            slugify(urllib.parse.unquote(epg.url.encoded_string())): EPGApiHealthResponse(
                time_since_last_updated=epg.get_time_since_last_update(),
                time_until_next_update=epg.get_time_until_next_update(),
            )
            for epg in self._epgs
        }

        time_until_next_update = self._next_update_time - datetime.now(tz=UTC)
        return EPGApiHandlerHealthResponse(
            time_until_next_update=time_until_next_update,
            tvg_ids=self._set_of_tvg_ids,
            epgs=epgs,
        )

    def get_tvg_epg_mappings(self) -> TVGEPGMappingsResponse:
        """Get the mapping of TVG IDs to their source EPG URLs."""
        return TVGEPGMappingsResponse(root=self._tvg_epg_mappings)

    # region Thread
    def _get_time_to_next_update(self) -> timedelta:
        """Get the time until the next EPG update."""
        wait_time = EPG_LIFESPAN

        for epg in self._epgs:
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

    def update_epgs(self, epg_conf_list: list[EPGInstanceConf]) -> None:  # noqa: C901 I split it up within the function
        """Update all EPGs with the current instance path."""

        async def _safe_update_epg(epg: EPG) -> bool:
            """Safely update a single EPG with exception handling."""
            try:
                return await epg.update()
            except Exception:
                logger.exception("Failed to update EPG %s", epg.url)
                return False

        async def _update_epgs_async() -> bool:
            """Asynchronous function to update EPGs."""
            any_epg_updated = False
            tasks = [_safe_update_epg(epg) for epg in self._epgs]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.exception("Failed to update EPG %s: %s", self._epgs[i].url, result)
                elif result:
                    any_epg_updated = True

            return any_epg_updated

        def _start_epg_update_thread() -> None:
            """Thread function to update EPGs."""
            logger.info("EPGHandler has %d EPGs starting EPG update thread [%s]", len(self._epgs), self._instance_id)
            while not self._stop_event.is_set():
                epg_actually_updated = asyncio.run(_update_epgs_async())

                if epg_actually_updated:
                    if self._stop_event.wait(10):  # Wait 10s or until stop is signaled
                        break
                    try:
                        logger.info("There are epg updates, condensing EPGs now.")
                        self._condense_epgs()
                    except Exception:
                        logger.exception("Failed to condense EPGs")

                time_until_next_update = self._get_time_to_next_update()
                self._next_update_time = datetime.now(tz=UTC) + time_until_next_update

                # Use wait instead of sleep so we can be interrupted
                if self._stop_event.wait(time_until_next_update.total_seconds()):
                    break

        self.stop_all_threads()

        self._epgs.clear()
        for epg_conf in epg_conf_list:
            self._epgs.append(EPG(epg_conf=epg_conf))

        thread = threading.Thread(target=_start_epg_update_thread, name="EPGHandler: update_epgs", daemon=True)
        thread.start()
        self._threads.append(thread)

    def stop_all_threads(self) -> None:
        """Stop all threads in the AcePool."""
        if len(self._threads) == 0:
            return

        logger.info("Stopping all %s threads [%s]", self.__class__.__name__, self._instance_id)
        self._stop_event.set()
        for thread in self._threads.copy():
            if thread.is_alive():
                thread.join(timeout=60)
                if not thread.is_alive():
                    self._threads.remove(thread)
                else:
                    logger.warning("Thread %s did not stop in time.", thread.name)

        self._stop_event.clear()
