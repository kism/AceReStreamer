"""Scraper object."""

from pathlib import Path
from typing import TYPE_CHECKING

from .config import AceScrapeSettings
from .logger import get_logger
from .scraper_health import AceQuality
from .scraper_html import scrape_streams_html_sites

if TYPE_CHECKING:
    from .scraper_objects import FoundAceStreams

logger = get_logger(__name__)


class AceScraper:
    """Scraper object."""

    def __init__(self, ace_scrape_settings: AceScrapeSettings, ace_quality_cache_path: Path | None) -> None:
        """Init MyCoolObject."""
        self.scrape_interval = ace_scrape_settings.scrape_interval
        self.disallowed_words = ace_scrape_settings.disallowed_words
        self.site_list_html = ace_scrape_settings.site_list_html
        self.streams: list[FoundAceStreams] = []
        self._ace_quality = AceQuality(ace_quality_cache_path)

        self.streams.extend(
            scrape_streams_html_sites(
                sites=self.site_list_html,
                disallowed_words=self.disallowed_words,
            )
        )

        self.print_streams()

    def get_streams(self) -> list[dict[str, str]]:
        """Get the found streams as a list of JSON strings."""
        streams = [stream.model_dump() for stream in self.streams]

        for found_stream in streams:
            for stream in found_stream["stream_list"]:
                stream["quality"] = self._ace_quality.get_quality(stream["ace_id"])

        return streams

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

        msg = "Found AceStreams:\n"
        for found_streams in self.streams:
            msg += f"Site: {found_streams.site_name}\n"
            for stream in found_streams.stream_list:
                msg += f"  - {stream.title} ({stream.ace_id})\n"
        logger.info(msg)
