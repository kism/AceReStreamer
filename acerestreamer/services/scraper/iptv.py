"""Scraper for IPTV sites to find AceStream streams."""

from pathlib import Path

import requests

from acerestreamer.config.models import ScrapeSiteIPTV, TitleFilter
from acerestreamer.utils.helpers import check_valid_ace_id
from acerestreamer.utils.logger import get_logger

from .cache import ScraperCache
from .name_processor import StreamNameProcessor
from .objects import FoundAceStream, FoundAceStreams

logger = get_logger(__name__)


class IPTVStreamScraper:
    """Scraper for IPTV sites to find AceStream streams."""

    def __init__(self) -> None:
        """Initialize the IPTVStreamScraper with the instance path."""
        self.scraper_cache: ScraperCache = ScraperCache()
        self.name_processor: StreamNameProcessor = StreamNameProcessor()

    def load_config(self, instance_path: Path, stream_name_processor: StreamNameProcessor) -> None:
        """Initialize the IPTVStreamScraper with the instance path."""
        self.name_processor = stream_name_processor
        self.scraper_cache.load_config(instance_path=instance_path)

    def scrape_streams_iptv_sites(self, sites: list[ScrapeSiteIPTV]) -> list[FoundAceStreams]:
        """Scrape the streams from the configured IPTV sites."""
        found_streams: list[FoundAceStreams] = []

        for site in sites:
            streams = self.scrape_streams_iptv_site(site)
            if streams:
                found_streams.append(streams)

        return found_streams

    def _parse_extinf_line(self, line: str, title_filter: TitleFilter) -> str:
        """Parse EXTINF line and return title if valid."""
        extinf_parts = 2
        parts = line.split(",", 1)  # Split on first comma only
        if len(parts) != extinf_parts:
            logger.warning("Malformed EXTINF line: %s", line)
            return ""

        title = parts[1].strip()

        if not self.name_processor.check_title_allowed(title=title, title_filter=title_filter):
            return ""

        return self.name_processor.cleanup_candidate_title(title)

    def _create_ace_stream_from_url(self, url: str, title: str) -> FoundAceStream | None:
        """Create FoundAceStream from URL and title if valid."""
        ace_id = self.name_processor.extract_ace_id_from_url(url)
        tvg_id = self.name_processor.get_tvg_id_from_title(title)

        if not check_valid_ace_id(ace_id):
            logger.warning("Invalid Ace ID found in candidate: %s, skipping", ace_id)
            return None

        return FoundAceStream(title=title, ace_id=ace_id, tvg_id=tvg_id)

    def _parse_m3u_content(self, content: str, site: ScrapeSiteIPTV) -> list[FoundAceStream]:
        """Parse M3U content and extract AceStream entries."""
        found_streams: list[FoundAceStream] = []
        lines = content.splitlines()

        current_title = ""

        for line in lines:
            line_normalised = line.replace("#EXTINF:-1,", "#EXTINF:-1").strip()

            if line.startswith("#EXTINF:"):
                current_title = self._parse_extinf_line(line_normalised, site.title_filter)
            elif self.name_processor.check_valid_ace_url(line_normalised) and current_title:
                ace_stream = self._create_ace_stream_from_url(line_normalised, current_title)
                if ace_stream:
                    found_streams.append(ace_stream)
                    current_title = ""  # Reset after successful match

        return found_streams

    def _get_site_content(self, site: ScrapeSiteIPTV) -> str | None:
        """Get site content from cache or by scraping."""
        cached_content = self.scraper_cache.load_from_cache(site.url)

        if self.scraper_cache.is_cache_valid(site.url):
            return cached_content

        logger.debug("Scraping streams from IPTV site: %s", site)
        try:
            response = requests.get(site.url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            error_short = type(e).__name__
            logger.error("Error scraping IPTV site %s, %s", site.url, error_short)  # noqa: TRY400
            return None

        response.encoding = "utf-8"
        content = response.text
        self.scraper_cache.save_to_cache(site.url, content)

        return content

    def scrape_streams_iptv_site(self, site: ScrapeSiteIPTV) -> FoundAceStreams | None:
        """Scrape the streams from the configured IPTV sites."""
        content = self._get_site_content(site)
        if not content:
            return None

        found_streams = self._parse_m3u_content(content, site)

        logger.debug("Found %d streams on IPTV site %s", len(found_streams), site.name)

        return (
            FoundAceStreams(
                site_name=site.name,
                site_slug=site.slug,
                stream_list=found_streams,
            )
            if found_streams
            else None
        )
