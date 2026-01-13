"""Scraper object."""

import asyncio
import contextlib
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp
from pydantic import HttpUrl

from acere.core.config import HTMLScraperFilter
from acere.database.handlers import (
    AceQualityCacheHandler,
    CategoryXCCategoryIDDatabaseHandler,
    ContentIdInfohashDatabaseHandler,
    ContentIdXCIDDatabaseHandler,
)
from acere.services.epg import EPGHandler
from acere.services.xc.models import XCStream
from acere.utils.logger import get_logger

from .api import APIStreamScraper
from .helpers import create_extinf_line, create_unique_stream_list
from .html import HTMLStreamScraper
from .iptv import IPTVStreamScraper
from .models import AceScraperSourceApi, FoundAceStream, FoundAceStreamAPI
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

_async_background_tasks: set[asyncio.Task[None]] = set()


class AceScraper:
    """Scraper object."""

    # region Initialization
    def __init__(self, instance_id: str = "") -> None:
        """Init the scraper."""
        self._instance_id = instance_id
        logger.debug("Initializing AceScraper (%s)", self._instance_id)
        self.external_url: HttpUrl | None = None
        self.ace_url: HttpUrl | None = None
        self.streams: dict[str, FoundAceStream] = {}
        self._ace_quality = AceQualityCacheHandler()
        self.epg_handler: EPGHandler = EPGHandler()
        self.stream_name_processor: StreamNameProcessor = StreamNameProcessor()
        self.html_scraper: HTMLStreamScraper = HTMLStreamScraper()
        self.iptv_scraper: IPTVStreamScraper = IPTVStreamScraper()
        self.api_scraper: APIStreamScraper = APIStreamScraper()
        self.currently_checking_quality: bool = False
        self._content_id_infohash_mapping = ContentIdInfohashDatabaseHandler()
        self._content_id_xc_id_mapping = ContentIdXCIDDatabaseHandler()
        self._category_xc_category_id_mapping = CategoryXCCategoryIDDatabaseHandler()
        self._scrape_threads: list[threading.Thread] = []

    def load_config(
        self,
        ace_scrape_conf: AceScrapeConf,
        epg_conf_list: list[EPGInstanceConf],
        instance_path: Path | str,
        external_url: HttpUrl | str,
        ace_url: HttpUrl,
    ) -> None:
        """Load the configuration for the scraper."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)

        if isinstance(external_url, str):
            external_url = HttpUrl(external_url)

        self.external_url = external_url
        self.ace_url = ace_url
        self._ace_quality.clean_table()
        self.epg_handler.load_config(epg_conf_list=epg_conf_list, instance_path=instance_path)

        self._config = ace_scrape_conf

        self.stream_name_processor.load_config(
            instance_path=instance_path,
            name_replacements=ace_scrape_conf.name_replacements,
            category_mapping=ace_scrape_conf.category_mapping,
        )
        self.html_scraper.load_config(
            instance_path=instance_path,
            stream_name_processor=self.stream_name_processor,
        )
        self.iptv_scraper.load_config(
            instance_path=instance_path,
            stream_name_processor=self.stream_name_processor,
        )
        self.api_scraper.load_config(
            instance_path=instance_path,
            stream_name_processor=self.stream_name_processor,
        )
        self._content_id_infohash_mapping.load(ace_url=ace_url)

    # region Scrape
    def start_scrape_thread(self) -> None:
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
                self._populate_infohashes()

                # Populate ourself
                self._print_streams()

                # EPGs
                tvg_id_list = [stream.tvg_id for stream in self.streams.values()]
                self.epg_handler.add_tvg_ids(tvg_ids=tvg_id_list)

                # For streams with only an infohash, populate the content_id using the api
                for _ in range(2):
                    missing_content_id_streams = [
                        stream for stream in found_streams if not stream.content_id and stream.infohash
                    ]
                    if len(missing_content_id_streams) == 0:
                        break

                    newly_populated_streams = async_loop.run_until_complete(
                        self._populate_missing_content_ids(missing_content_id_streams)
                    )
                    if len(newly_populated_streams) != 0:
                        self.streams = create_unique_stream_list(list(self.streams.values()) + newly_populated_streams)
                        break
                    time.sleep(60)

                self.mark_alternate_streams()

                self.print_warnings()
                time.sleep(SCRAPE_INTERVAL)

        for thread in self._scrape_threads:
            thread.join(timeout=1)

        thread = threading.Thread(target=run_scrape_thread, name="AceScraper: run_scrape", daemon=True)
        thread.start()

        self._scrape_threads = [thread]

    # region GET API
    def get_stream_by_content_id_api(self, content_id: str) -> FoundAceStreamAPI | None:
        """Get a stream by its Ace ID, will use the first found matching FoundAceStreamAPI by content_id."""
        if content_id in self.streams:
            stream = self.streams[content_id]
            program_title, program_description = self.epg_handler.get_current_program(tvg_id=stream.tvg_id)

            return FoundAceStreamAPI(
                site_names=stream.site_names,
                quality=self._ace_quality.get_quality(content_id).quality,
                has_ever_worked=self._ace_quality.get_quality(content_id).has_ever_worked,
                title=stream.title,
                content_id=stream.content_id,
                infohash=stream.infohash,
                tvg_id=stream.tvg_id,
                tvg_logo=stream.tvg_logo,
                program_title=program_title,
                program_description=program_description,
            )

        return None

    def get_stream_list_api(self) -> list[FoundAceStreamAPI]:
        """Get a list of streams, as a list of dicts, deduplicated by content_id."""
        return [
            stream
            for content_id in self.streams
            if (stream := self.get_stream_by_content_id_api(content_id=content_id)) is not None
        ]

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

    def get_streams_health(self) -> dict[str, Quality]:
        """Get the health of the streams."""
        return self._ace_quality.get_all()

    # region GET API XC
    def get_content_id_by_xc_id(self, xc_id: int) -> str | None:
        """Get the content ID by XC ID."""
        return self._content_id_xc_id_mapping.get_content_id(xc_id=xc_id)

    def get_content_id_by_tvg_id(self, tvg_id: str) -> str | None:
        """Get the content ID by TVG ID."""
        for stream in self.streams.values():
            if stream.tvg_id == tvg_id:
                return stream.content_id
        return None

    # region GET IPTV
    def get_streams_as_iptv(self, token: str) -> str:
        """Get the found streams as an IPTV M3U8 string."""
        if not self.external_url:
            logger.error("External URL is not set, cannot generate IPTV streams.")
            return ""

        # There are a few standards for the tag for the tvg url, most to least common x-tvg-url, url-tvg, tvg-url
        epg_url = HttpUrl(f"{self.external_url}epg")
        m3u8_content = f'#EXTM3U x-tvg-url="{epg_url}" url-tvg="{epg_url}" refresh="3600"\n'

        iptv_set = set()

        # I used to filter this for whether the stream has ever worked,
        # but sometimes sites change the id of their stream often...
        for stream in self.streams.values():
            logger.debug(stream)

            external_url_tvg = HttpUrl(self.external_url.encoded_string() + "tvg-logo/")

            line_one = create_extinf_line(stream, tvg_url_base=external_url_tvg, token=token)
            line_two = f"{self.external_url}hls/{stream.content_id}"
            if token:
                line_two += f"?token={token}"

            iptv_set.add(line_one + line_two)

        return m3u8_content + "\n".join(sorted(iptv_set))

    def get_streams_as_iptv_xc(
        self,
        xc_category_filter: int | None,
        token: str = "",
    ) -> list[XCStream]:
        """Get the found streams as a list of XCStream objects."""
        streams: list[XCStream] = []

        token_str = "" if token == "" else f"?token={token}"

        current_stream_number = 1
        for stream in self.streams.values():
            xc_id = self._content_id_xc_id_mapping.get_xc_id(stream.content_id)
            xc_category_id = self._category_xc_category_id_mapping.get_xc_category_id(stream.group_title)
            if xc_category_filter is None or xc_category_id == xc_category_filter:
                streams.append(
                    XCStream(
                        num=current_stream_number,
                        name=stream.title,
                        stream_id=xc_id,
                        stream_icon=f"{self.external_url}tvg-logo/{stream.tvg_logo}{token_str}"
                        if stream.tvg_logo
                        else "",
                        epg_channel_id=stream.tvg_id,
                        category_id=str(xc_category_id),
                    )
                )
            current_stream_number += 1

        return streams

    # region Quality
    def increment_quality(self, content_id: str, m3u_playlist: str = "") -> None:
        """Increment the quality of a stream by content_id."""
        self._ace_quality.increment_quality(content_id=content_id, m3u_playlist=m3u_playlist)

    async def check_missing_quality(self) -> bool:
        """Check the quality of all streams.

        This is an async function since threading doesn't get app context no matter how hard I try.
        Bit of a hack.
        """
        from acere.api.routes.hls import hls  # Avoid circular import  # noqa: PLC0415

        if self.currently_checking_quality:
            return False

        async def check_missing_quality_thread(base_url: HttpUrl) -> None:
            try:
                self.currently_checking_quality = True
                await asyncio.sleep(0)  # This await means the task returns faster I think

                streams = self.get_stream_list_api()  # API method gets the health information
                if not streams:
                    logger.warning("No streams found to check quality.")
                    self.currently_checking_quality = False
                    return

                ace_streams_never_worked = len(
                    [  # We also check if the quality is zero, since maybe it started working
                        content_id
                        for content_id, stream in self._ace_quality.get_all().items()
                        if not stream.has_ever_worked or stream.quality == 0
                    ]
                )

                # We only iterate through streams from get_stream_list_api()
                # since we don't want to health check streams that are not current per the scraper.
                # Don't enumerate here, and don't bother with list comprehension tbh
                n = 0
                for stream in streams:
                    if not stream.has_ever_worked or stream.quality == 0:
                        n += 1
                        stream_url = f"{base_url}/{stream.content_id}"
                        logger.info(
                            "Checking Ace Stream %s (%d/%d)",
                            stream_url,
                            n,
                            ace_streams_never_worked,
                        )

                        for _ in range(3):
                            with contextlib.suppress(
                                aiohttp.ClientError,
                                asyncio.TimeoutError,
                            ):
                                await hls(path=stream.content_id, authentication_override=True)
                            await asyncio.sleep(1)

                        await asyncio.sleep(10)
            except Exception:  # noqa: BLE001 This is a background task so it won't crash the app
                exception_name = Exception.__name__
                logger.warning("Exception occurred during quality check: %s", exception_name)

            self.currently_checking_quality = False

        url = f"{self.external_url}hls"

        task = asyncio.create_task(check_missing_quality_thread(base_url=HttpUrl(url)))
        _async_background_tasks.add(task)
        task.add_done_callback(_async_background_tasks.discard)

        return True

    # region Helpers
    def _print_streams(self) -> None:
        """Print the found streams."""
        if not self.streams:
            logger.warning("Scraper found no AceStreams.")
            return

        n = len(self.streams)
        msg = f"Found AceStreams: {n} unique streams across {len(self.streams)} site definitions."
        logger.info(msg)

    def _populate_infohashes(self) -> None:
        """Populate infohashes for streams that have a content ID."""
        for stream in self.streams.values():
            if not stream.infohash:
                stream.infohash = self._content_id_infohash_mapping.get_infohash(
                    content_id=stream.content_id,
                )

    async def _populate_missing_content_ids(self, streams: list[FoundAceStream]) -> list[FoundAceStream]:
        """Populate missing content IDs for streams that have an infohash."""
        populated_streams: list[FoundAceStream] = []

        for stream in streams:
            if not stream.content_id:
                stream.content_id = self._content_id_infohash_mapping.get_content_id(
                    infohash=stream.infohash,
                )
                if stream.content_id:
                    populated_streams.append(stream)

        for stream in streams:
            if not stream.content_id:
                stream.content_id = await self._content_id_infohash_mapping.populate_from_api(
                    infohash=stream.infohash,
                )
                if not stream.content_id:
                    logger.error(
                        "Failed to populate content ID for stream with infohash %s, skipping",
                        stream.infohash,
                    )
                else:
                    populated_streams.append(stream)

        return populated_streams

    def print_warnings(self) -> None:
        """Print warnings for the state of self.streams, specifically for duplicates."""
        unique_tvg_ids = set()
        unique_infohashes = set()
        unique_names = set()
        for stream in self.streams.values():
            if stream.tvg_id and stream.tvg_id in unique_tvg_ids:
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

    def mark_alternate_streams(self) -> None:
        """Iterates through streams and for any identical title, for duplicates mark the titles with a stream number."""
        results: dict[str, list[FoundAceStream]] = {}  # Title, list of streams with that title

        for stream in self.streams.values():
            results[stream.title] = [*results.get(stream.title, []), stream]

        for streams in results.values():
            if len(streams) <= 1:
                continue

            # Sort by xc_id, will approximatly be by date discovered
            streams.sort(
                key=lambda s: self._content_id_xc_id_mapping.get_xc_id(s.content_id) or 0,
            )

            # Mark all but the first as alternate
            for n, stream in enumerate(streams):
                stream.title += f" #{n + 1}"
