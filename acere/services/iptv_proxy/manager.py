"""IPTV Proxy Manager — orchestrates scraping and URL mapping."""

import asyncio
import hashlib
import threading
from typing import TYPE_CHECKING

from acere.instances.config import settings
from acere.instances.iptv_streams import get_iptv_streams_db_handler
from acere.utils.logger import get_logger

from .scraper import IPTVProxyScraper

if TYPE_CHECKING:
    from acere.services.scraper.models import FoundIPTVStream
else:
    FoundIPTVStream = object

logger = get_logger(__name__)

SCRAPE_INTERVAL = 60 * 60  # 1 hour


class IPTVProxyManager:
    """Manages IPTV proxy streams: scraping, URL mapping, and lifecycle."""

    def __init__(self, instance_id: str = "") -> None:
        """Initialize the IPTV proxy manager."""
        self._instance_id = instance_id
        self._threads: list[threading.Thread] = []
        self._stop_event = threading.Event()
        self._scraper = IPTVProxyScraper()
        self._url_map: dict[str, str] = {}

    def get_upstream_url(self, slug: str) -> str | None:
        """Look up the upstream HLS URL for a given slug."""
        url = self._url_map.get(slug)
        if url:
            return url

        # Fall back to database
        handler = get_iptv_streams_db_handler()
        entry = handler.get_by_slug(slug)
        if entry:
            self._url_map[slug] = entry.upstream_url
            return entry.upstream_url
        return None

    def get_segment_upstream_url(self, slug: str, segment: str) -> str | None:
        """Given a stream slug and segment filename, build the upstream segment URL."""
        upstream = self.get_upstream_url(slug)
        if not upstream:
            return None
        # Replace the playlist filename with the segment path
        base_url = upstream.rsplit("/", 1)[0]
        return f"{base_url}/{segment}"

    @staticmethod
    def make_slug(upstream_url: str) -> str:
        """Create a stable, URL-safe slug from an upstream URL."""
        return hashlib.sha256(upstream_url.encode()).hexdigest()[:16]

    def start_scrape_thread(self) -> None:
        """Start the background scraping thread."""
        iptv_conf = settings.iptv
        if not iptv_conf.xtream and not iptv_conf.m3u8:
            logger.info("No IPTV proxy sources configured, skipping scrape thread")
            return

        def run_scrape_thread() -> None:
            async_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(async_loop)

            while not self._stop_event.is_set():
                logger.info("Running IPTV proxy scraper [%s]", self._instance_id)

                async def scrape_all() -> list[FoundIPTVStream]:
                    tasks = [self._scraper.scrape_m3u8_source(source) for source in settings.iptv.m3u8]
                    tasks.extend(self._scraper.scrape_xtream_source(source) for source in settings.iptv.xtream)

                    all_results = await asyncio.gather(*tasks, return_exceptions=True)

                    found_streams: list[FoundIPTVStream] = []
                    for result in all_results:
                        if isinstance(result, list):
                            found_streams.extend(result)
                        else:
                            logger.error("Error occurred while scraping IPTV: %s", result)

                    return found_streams

                found_streams = async_loop.run_until_complete(scrape_all())

                # Apply max_active_streams limits per source
                found_streams = self._apply_stream_limits(found_streams)

                # Write to database and update URL map
                self._write_streams_to_database(found_streams)

                logger.info("IPTV proxy scraper found %d total streams", len(found_streams))

                if self._stop_event.wait(SCRAPE_INTERVAL):
                    break

        self.stop_all_threads()

        thread = threading.Thread(target=run_scrape_thread, name="IPTVProxyManager: run_scrape", daemon=True)
        thread.start()
        self._threads.append(thread)

    def stop_all_threads(self) -> None:
        """Stop all threads."""
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

    def _apply_stream_limits(self, streams: list[FoundIPTVStream]) -> list[FoundIPTVStream]:
        """Apply max_active_streams limits per source."""
        # Build a map of source_name -> max_active_streams
        limits: dict[str, int] = {}
        for m3u8_source in settings.iptv.m3u8:
            if m3u8_source.max_active_streams > 0:
                limits[m3u8_source.name] = m3u8_source.max_active_streams
        for xtream_source in settings.iptv.xtream:
            if xtream_source.max_active_streams > 0:
                limits[xtream_source.name] = xtream_source.max_active_streams

        if not limits:
            return streams

        # Count streams per source and filter
        counts: dict[str, int] = {}
        filtered: list[FoundIPTVStream] = []
        for stream in streams:
            source_name = stream.source_name
            current_count = counts.get(source_name, 0)
            max_count = limits.get(source_name, 0)
            if max_count > 0 and current_count >= max_count:
                continue
            counts[source_name] = current_count + 1
            filtered.append(stream)

        return filtered

    def _write_streams_to_database(self, streams: list[FoundIPTVStream]) -> None:
        """Write found streams to the database and update URL map."""
        handler = get_iptv_streams_db_handler()

        self._url_map.clear()

        for stream in streams:
            slug = self.make_slug(stream.upstream_url)
            handler.update_stream(stream=stream, slug=slug)
            self._url_map[slug] = stream.upstream_url
