"""IPTV Proxy Manager — orchestrates scraping and URL mapping."""

import asyncio
import hashlib
import threading
from typing import TYPE_CHECKING

from acere.instances.config import settings
from acere.instances.epg import get_epg_handler
from acere.instances.iptv_streams import get_iptv_streams_db_handler
from acere.instances.xc_stream_map import get_xc_stream_map_handler
from acere.services.iptv_proxy.pool import IPTVPoolManager
from acere.services.scraper.iptv import IPTVProxyScraper
from acere.utils.logger import get_logger

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
        self.pool = IPTVPoolManager(instance_id=instance_id)

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
        """Given a stream slug and segment path, build the upstream segment URL."""
        upstream = self.get_upstream_url(slug)
        if not upstream:
            return None

        if "/" in segment:
            # Multi-component path (root-relative) — use the upstream server origin
            from urllib.parse import urlparse  # noqa: PLC0415

            parsed = urlparse(upstream)
            return f"{parsed.scheme}://{parsed.netloc}/{segment}"

        # Simple filename — relative to the playlist directory
        base_url = upstream.rsplit("/", 1)[0]
        return f"{base_url}/{segment}"

    def update_upstream_url(self, slug: str, url: str) -> None:
        """Update the in-memory URL map entry for a slug (e.g. after following a redirect)."""
        self._url_map[slug] = url

    def check_stream_allowed(self, slug: str) -> bool:
        """Check if a stream is allowed by the pool. Returns True if allowed."""
        source_name = self._get_source_name_for_slug(slug)
        if source_name is None:
            return True  # Unknown stream, allow (will 404 later anyway)
        return self.pool.check_in(slug, source_name)

    def _get_source_name_for_slug(self, slug: str) -> str | None:
        """Get the source name for a slug from the database."""
        handler = get_iptv_streams_db_handler()
        entry = handler.get_by_slug(slug)
        return entry.source_name if entry else None

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

                async def scrape_all() -> tuple[list[FoundIPTVStream], set[str]]:
                    source_names = [s.name for s in settings.iptv.m3u8] + [s.name for s in settings.iptv.xtream]
                    tasks = [self._scraper.scrape_m3u8_source(source) for source in settings.iptv.m3u8]
                    tasks.extend(self._scraper.scrape_xtream_source(source) for source in settings.iptv.xtream)

                    all_results = await asyncio.gather(*tasks, return_exceptions=True)

                    found_streams: list[FoundIPTVStream] = []
                    scraped_source_names: set[str] = set()
                    for source_name, result in zip(source_names, all_results, strict=False):
                        if isinstance(result, list):
                            found_streams.extend(result)
                            scraped_source_names.add(source_name)
                        else:
                            logger.error("Error occurred while scraping IPTV source '%s': %s", source_name, result)

                    return found_streams, scraped_source_names

                found_streams, scraped_source_names = async_loop.run_until_complete(scrape_all())

                # Write to database and update URL map
                self._write_streams_to_database(found_streams, scraped_source_names)

                logger.info("IPTV proxy scraper found %d total streams", len(found_streams))

                if self._stop_event.wait(SCRAPE_INTERVAL):
                    break

        self.stop_all_threads()

        self.pool.start_cleanup_thread()

        thread = threading.Thread(target=run_scrape_thread, name="IPTVProxyManager: run_scrape", daemon=True)
        thread.start()
        self._threads.append(thread)

    def stop_all_threads(self) -> None:
        """Stop all threads."""
        self.pool.stop_all_threads()

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

    def _write_streams_to_database(self, streams: list[FoundIPTVStream], scraped_source_names: set[str]) -> None:
        """Write found streams to the database and update URL map."""
        handler = get_iptv_streams_db_handler()
        xc_handler = get_xc_stream_map_handler()

        self._url_map.clear()

        current_slugs: set[str] = set()
        current_slugs_by_source: dict[str, set[str]] = {}
        tvg_ids_to_add: set[str] = set()
        for stream in streams:
            tvg_ids_to_add.add(stream.tvg_id)
            slug = self.make_slug(stream.upstream_url)
            handler.update_stream(stream=stream, slug=slug)
            self._url_map[slug] = stream.upstream_url
            current_slugs.add(slug)
            current_slugs_by_source.setdefault(stream.source_name, set()).add(slug)

        get_epg_handler().add_tvg_ids(tvg_ids=tvg_ids_to_add)

        # Remove stale entries for successfully scraped sources
        for source_name in scraped_source_names:
            source_current_slugs = current_slugs_by_source.get(source_name, set())
            stale_slugs = handler.get_slugs_by_source(source_name) - source_current_slugs
            for slug in stale_slugs:
                logger.info("Removing stale IPTV stream (slug: %s) from source '%s'", slug, source_name)
                handler.delete_by_slug(slug)

        # Register all current IPTV slugs in XC stream map and cleanup stale entries
        xc_handler.register_keys("iptv", current_slugs)
        xc_handler.delete_by_type_and_keys("iptv", current_slugs)
