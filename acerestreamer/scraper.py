"""Scraper object."""

import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

from .config import AceScrapeConf
from .logger import get_logger
from .scraper_health import AceQuality
from .scraper_html import scrape_streams_html_sites
from .scraper_iptv import scrape_streams_iptv_sites
from .scraper_objects import FlatFoundAceStream, FoundAceStreams

if TYPE_CHECKING:
    from .config import ScrapeSiteHTML, ScrapeSiteIPTV
else:
    ScrapeSiteHTML = object
    ScrapeSiteIPTV = object

logger = get_logger(__name__)

SCRAPE_INTERVAL = 60 * 60  # Default scrape interval in seconds (1 hour)


class AceScraperSourcesApi(BaseModel):
    """Represent the sources of the AceScraper, for API use."""

    html: list[ScrapeSiteHTML]
    iptv_m3u8: list[ScrapeSiteIPTV]


class AceScraperSourceApi(BaseModel):
    """Represent a scraper instance, generic for HTML and IPTV sources."""

    name: str
    slug: str
    epg: list[str] = []


class AceScraper:
    """Scraper object."""

    def __init__(self, ace_scrape_settings: AceScrapeConf | None, instance_path: Path | None) -> None:
        """Init MyCoolObject."""
        self._ace_quality_cache_path = instance_path / "ace_quality_cache.json" if instance_path else None

        self.streams: list[FoundAceStreams] = []

        self.html: list[ScrapeSiteHTML] = []
        self.iptv_m3u8: list[ScrapeSiteIPTV] = []

        if ace_scrape_settings:
            self.html = ace_scrape_settings.html
            self.iptv_m3u8 = ace_scrape_settings.iptv_m3u8

        self._ace_quality = AceQuality(self._ace_quality_cache_path)

        if self._ace_quality_cache_path:
            self.run_scrape()

    def run_scrape(self) -> None:
        """Run the scraper to find AceStreams."""

        def run_scrape_thread() -> None:
            """Thread function to run the scraper."""
            while True:
                logger.info("Running AceStream scraper...")

                self.streams.extend(
                    scrape_streams_html_sites(
                        sites=self.html,
                    )
                )

                self.streams.extend(
                    scrape_streams_iptv_sites(
                        sites=self.iptv_m3u8,
                    )
                )

                self.print_streams()
                time.sleep(SCRAPE_INTERVAL)

        threading.Thread(target=run_scrape_thread, name="AceScraperThread", daemon=True).start()

    def get_stream_by_ace_id(self, ace_id: str) -> FlatFoundAceStream:
        """Get a stream by its Ace ID, will use the first found matching FlatFoundAceStream by ace_id."""
        streams = self.get_streams_flat()
        for found_stream in streams:
            if found_stream.ace_id == ace_id:
                return found_stream

        return FlatFoundAceStream(
            site_name="Unknown",
            quality=self._ace_quality.default_quality,
            title=ace_id,
            ace_id=ace_id,
        )

    def get_all_streams_by_source(self) -> list[FoundAceStreams]:
        """Get the found streams as a list of dicts, ready to be turned into json."""
        streams = list(self.streams)

        for found_stream in streams:
            for stream in found_stream.stream_list:
                stream.quality = self._ace_quality.get_quality(stream.ace_id)

        return streams

    def get_streams_by_source(self, source_slug: str) -> list[FlatFoundAceStream] | None:
        """Get the found streams for a specific source by its slug."""
        for scraped_streams_listing in self.streams:
            if scraped_streams_listing.site_slug == source_slug:
                return [
                    FlatFoundAceStream(
                        site_name=scraped_streams_listing.site_name,
                        quality=self._ace_quality.get_quality(stream.ace_id),
                        title=stream.title,
                        ace_id=stream.ace_id,
                    )
                    for stream in scraped_streams_listing.stream_list
                ]

        logger.warning("No scraper source found with slug: %s", source_slug)
        return None

    def get_streams_flat(self) -> list[FlatFoundAceStream]:
        """Get a list of streams, as a list of dicts."""
        streams = [stream.model_dump() for stream in self.streams]

        flat_streams: list[FlatFoundAceStream] = []
        for found_stream in streams:
            for stream in found_stream["stream_list"]:
                new_stream: FlatFoundAceStream = FlatFoundAceStream(
                    site_name=found_stream["site_name"],
                    quality=self._ace_quality.get_quality(stream["ace_id"]),
                    title=stream["title"],
                    ace_id=stream["ace_id"],
                )
                flat_streams.append(new_stream)
        return flat_streams

    def get_streams_sources(self) -> AceScraperSourcesApi:
        """Get the sources for the scraper."""
        return AceScraperSourcesApi(
            html=self.html,
            iptv_m3u8=self.iptv_m3u8,
        )

    def get_streams_sources_flat(self) -> list[AceScraperSourceApi]:
        """Get the sources for the scraper, as a flat list."""
        return [AceScraperSourceApi(name=site.name, slug=site.slug) for site in self.html + self.iptv_m3u8]

    def get_streams_source(self, slug: str) -> AceScraperSourceApi | None:
        """Get a source by its slug."""
        for site in self.html + self.iptv_m3u8:
            if site.slug == slug:
                return AceScraperSourceApi(name=site.name, slug=site.slug)

        logger.warning("No scraper source found with slug: %s", slug)
        return None

    def get_streams_health(self) -> dict[str, int]:
        """Get the health of the streams."""
        return self._ace_quality.ace_streams

    def increment_quality(self, ace_id: str, rating: int) -> None:
        """Increment the quality of a stream by ace_id."""
        self._ace_quality.increment_quality(ace_id, rating)

    def print_streams(self) -> None:
        """Print the found streams."""
        if not self.streams:
            logger.warning("Scraper found no AceStreams.")
            return

        n = 0
        msg = "Found AceStreams: "
        for found_streams in self.streams:
            n = n + len(found_streams.stream_list)
        msg += f"{n} streams across {len(self.streams)} sites."
        logger.info(msg)
