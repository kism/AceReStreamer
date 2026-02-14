"""Scraper for IPTV sites to find AceStream streams."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import aiohttp

from acere.services.scraper.common import ScraperCommon
from acere.services.scraper.iptv.parser import M3UParser
from acere.services.scraper.models import FoundAceStream
from acere.utils.exception_handling import log_aiohttp_exception
from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from acere.core.config.scraper import ScrapeSiteIPTV
else:
    ScrapeSiteIPTV = object

logger = get_logger(__name__)


class IPTVStreamScraper(ScraperCommon):
    """Scraper for IPTV sites to find AceStream streams."""

    def __init__(self) -> None:
        """Initialize the IPTVStreamScraper with parser."""
        super().__init__()
        self._parser = M3UParser()

    async def scrape_iptv_playlists(self, sites: list[ScrapeSiteIPTV]) -> list[FoundAceStream]:
        """Scrape the streams from the configured IPTV sites."""
        found_streams: list[FoundAceStream] = []

        for site in sites:
            streams = await self._scrape_iptv_playlist(site)
            if streams:
                found_streams.extend(streams)

        return found_streams

    async def _scrape_iptv_playlist(self, site: ScrapeSiteIPTV) -> list[FoundAceStream]:
        """Scrape the streams from the configured IPTV sites."""
        content = await self._get_site_content(site)
        logger.trace("Scraping content for IPTV site %s: len=%d", site.name, len(content) if content else 0)
        if not content:
            return []

        found_streams = await self.parse_m3u_content(content, site)

        for stream in found_streams:  # These streams are freshly scraped
            stream.last_scraped_time = datetime.now(tz=UTC)

        logger.debug("Found %d streams on IPTV site %s", len(found_streams), site.name)

        return found_streams

    async def _get_site_content(self, site: ScrapeSiteIPTV) -> str | None:
        """Get site content from cache or by scraping."""
        if self.scraper_cache.is_cache_valid(site.url):
            logger.debug("Loaded IPTV site content from cache for: %s", site.name)
            return self.scraper_cache.load_from_cache(site.url)

        logger.info("Scraping streams from IPTV site: %s", site.name)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(site.url.encoded_string()) as response:
                    response.raise_for_status()
                    content = await response.text(encoding="utf-8")
        except (aiohttp.ClientError, TimeoutError) as e:
            log_aiohttp_exception(logger, site.url, e)
            return None

        logger.debug("Caching IPTV site content for: %s", site.name)
        self.scraper_cache.save_to_cache(site.url, content)

        return content

    async def parse_m3u_content(self, content: str, site: ScrapeSiteIPTV) -> list[FoundAceStream]:
        """Parse M3U content and extract AceStream entries.

        This method delegates to M3UParser for backward compatibility.
        """
        return await self._parser.parse_m3u_content(content, site)
