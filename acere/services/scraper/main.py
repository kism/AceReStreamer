"""Scraper object."""

import asyncio
import re
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from acere.core.config import HTMLScraperFilter
from acere.instances.ace_streams import get_ace_streams_db_handler
from acere.instances.epg import get_epg_handler
from acere.utils.logger import get_logger

from .api import APIStreamScraper
from .helpers import create_unique_stream_list, get_content_id_from_infohash_acestream_api
from .html import HTMLStreamScraper
from .iptv import IPTVStreamScraper
from .models import AceScraperSourceApi, FoundAceStream, ScraperSettings
from .name_processor import StreamNameProcessor

if TYPE_CHECKING:
    from acere.core.config import (
        AceScrapeConf,
        EPGInstanceConf,
        ScrapeSiteHTML,
        ScrapeSiteIPTV,
    )
    from acere.services.ace_quality import Quality
else:
    ScrapeSiteHTML = object
    ScrapeSiteIPTV = object
    EPGInstanceConf = object
    AceScrapeConf = object
    Quality = object

logger = get_logger(__name__)

SCRAPE_INTERVAL = 60 * 60  # Default scrape interval in seconds (1 hour)


_REGEX_STREAM_NUMBER = re.compile(r"#(\d+)$")


class AceScraper:
    """Scraper object."""

    # region Initialization
    def __init__(self, instance_id: str = "") -> None:
        """Init the scraper."""
        self._instance_id = instance_id
        logger.debug("Initializing AceScraper (%s)", self._instance_id)
        self.streams: dict[str, FoundAceStream] = {}
        self.stream_name_processor: StreamNameProcessor = StreamNameProcessor()
        self.html_scraper: HTMLStreamScraper = HTMLStreamScraper()
        self.iptv_scraper: IPTVStreamScraper = IPTVStreamScraper()
        self.api_scraper: APIStreamScraper = APIStreamScraper()
        self.currently_checking_quality: bool = False
        self._scrape_threads: list[threading.Thread] = []

    def load_config(
        self,
        ace_scrape_conf: AceScrapeConf,
        instance_path: Path | str,
    ) -> None:
        """Load the configuration for the scraper."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)

        self._config = ace_scrape_conf

        self.stream_name_processor.load_config(
            instance_path=instance_path,
            name_replacements=ace_scrape_conf.name_replacements,
            content_id_infohash_name_overrides=ace_scrape_conf.content_id_infohash_name_overrides,
            category_mapping=ace_scrape_conf.category_mapping,
        )
        scraper_settings: ScraperSettings = {
            "instance_path": instance_path,
            "stream_name_processor": self.stream_name_processor,
        }

        self.html_scraper.load_config(**scraper_settings)
        self.iptv_scraper.load_config(**scraper_settings)
        self.api_scraper.load_config(**scraper_settings)

    # region Scrape
    def start_scrape_thread(self) -> None:  # noqa: C901
        """Run the scraper to find AceStreams."""

        def run_scrape_thread() -> None:
            """Thread function to run the scraper."""
            async_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(async_loop)

            while True:
                logger.info("Running AceStream scraper (%s)", self._instance_id)

                async def find_streams() -> list[FoundAceStream]:
                    tasks = [
                        self.html_scraper.scrape_sites(sites=self._config.html),
                        self.iptv_scraper.scrape_iptv_playlists(sites=self._config.iptv_m3u8),
                        self.api_scraper.scrape_api_endpoints(sites=self._config.api),
                    ]

                    all_results = await asyncio.gather(*tasks, return_exceptions=True)

                    found_streams: list[FoundAceStream] = []
                    for result in all_results:
                        if isinstance(result, list):
                            found_streams.extend(result)
                        else:
                            logger.error("Error occurred while scraping: %s", result)

                    return found_streams

                found_streams = async_loop.run_until_complete(find_streams())

                self.streams = create_unique_stream_list(found_streams)

                # Populate ourself
                self._print_streams()

                # EPGs
                tvg_id_list = [stream.tvg_id for stream in self.streams.values()]
                get_epg_handler().add_tvg_ids(tvg_ids=tvg_id_list)

                # For streams with only an infohash, populate the content_id using the api
                for attempt in range(2):
                    # Check current streams for missing content_ids
                    missing_content_id_streams = [
                        stream for stream in found_streams if not stream.content_id and stream.infohash
                    ]
                    if len(missing_content_id_streams) == 0:
                        break

                    # Try to populate from database and API
                    async_loop.run_until_complete(self._populate_missing_content_ids(missing_content_id_streams))

                    # Re-create unique stream list after modification
                    self.streams = create_unique_stream_list(missing_content_id_streams + list(self.streams.values()))

                    # Check if there are still missing content_ids after population attempt
                    still_missing = [stream for stream in found_streams if not stream.content_id and stream.infohash]

                    if len(still_missing) == 0:
                        break

                    # Only sleep if we're going to retry
                    if attempt < 1:
                        logger.info(
                            "Still have %d streams with missing content_ids, retrying in 60 seconds", len(still_missing)
                        )
                        time.sleep(60)

                self._write_streams_to_database()

                self._print_warnings()
                time.sleep(SCRAPE_INTERVAL)

        for thread in self._scrape_threads:
            thread.join(timeout=1)

        thread = threading.Thread(target=run_scrape_thread, name="AceScraper: run_scrape", daemon=True)
        thread.start()

        self._scrape_threads = [thread]

    # region GET API Scraper
    def get_scraper_sources_flat_api(self) -> list[AceScraperSourceApi]:
        """Get the sources for the scraper, as a flat list."""
        sources = [
            AceScraperSourceApi(
                name=site.name,
                url=site.url,
                title_filter=site.title_filter,
                type="html",
                html_filter=HTMLScraperFilter(
                    check_sibling=site.html_filter.check_sibling,
                    target_class=site.html_filter.target_class,
                ),
            )
            for site in self._config.html
        ]

        sources.extend(
            [
                AceScraperSourceApi(
                    name=site.name,
                    url=site.url,
                    title_filter=site.title_filter,
                    type="iptv",
                )
                for site in self._config.iptv_m3u8
            ]
        )

        sources.extend(
            [
                AceScraperSourceApi(
                    name=site.name,
                    url=site.url,
                    title_filter=site.title_filter,
                    type="api",
                )
                for site in self._config.api
            ]
        )

        return sources

    # region Helpers
    def _print_streams(self) -> None:
        """Print the found streams."""
        if not self.streams:
            logger.warning("Scraper found no AceStreams.")
            return

        n = len(self.streams)
        msg = f"Found AceStreams: {n} unique streams across {len(self.streams)} site definitions."
        logger.info(msg)

    async def _populate_missing_content_ids(self, streams: list[FoundAceStream]) -> list[FoundAceStream]:
        """Populate missing content IDs for streams that have an infohash."""
        populated_streams: list[FoundAceStream] = []
        handler = get_ace_streams_db_handler()

        for stream in streams:
            if not stream.content_id and stream.infohash:
                tmp_content_id = handler.get_content_id_from_infohash(infohash=stream.infohash)
                if tmp_content_id:
                    stream.content_id = tmp_content_id

        for stream in streams:
            if not stream.content_id and stream.infohash:
                stream.content_id = await get_content_id_from_infohash_acestream_api(
                    infohash=stream.infohash,
                )
                if stream.content_id:
                    populated_streams.append(stream)

        return populated_streams

    def _print_warnings(self) -> None:
        """Print warnings for the state of self.streams, specifically for duplicates."""
        unique_tvg_ids = set()
        unique_infohashes = set()
        unique_names = set()
        for stream in self.streams.values():
            if (
                stream.tvg_id and stream.tvg_id in unique_tvg_ids and (not _REGEX_STREAM_NUMBER.search(stream.title))
            ):  # If it's not marked as an alternate stream
                logger.warning("Duplicate TVG ID found: %s", stream.tvg_id)

            unique_tvg_ids.add(stream.tvg_id)

            if stream.infohash and stream.infohash in unique_infohashes:
                logger.warning("Duplicate infohash found: %s", stream.infohash)
            unique_infohashes.add(stream.infohash)

            if stream.title and stream.title in unique_names:
                logger.warning("Duplicate name found: %s", stream.title)
            unique_names.add(stream.title)

        logger.info(
            "Scraper has %d unique TVG IDs, %d unique infohashes, and %d unique names.",
            len(unique_tvg_ids),
            len(unique_infohashes),
            len(unique_names),
        )

    def _write_streams_to_database(self) -> None:
        """Write the found streams to the database."""
        handler = get_ace_streams_db_handler()
        for stream in self.streams.values():
            handler.update_stream(stream=stream)
