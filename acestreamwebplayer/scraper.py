"""Scraper object."""

from pathlib import Path

from .config import AceScrapeSettings
from .logger import get_logger
from .scraper_health import AceQuality
from .scraper_html import scrape_streams_html_sites
from .scraper_iptv import scrape_streams_iptv_sites
from .scraper_objects import FlatFoundAceStream, FoundAceStreams

logger = get_logger(__name__)


class AceScraper:
    """Scraper object."""

    def __init__(self, ace_scrape_settings: AceScrapeSettings, ace_quality_cache_path: Path | None) -> None:
        """Init MyCoolObject."""
        self.streams: list[FoundAceStreams] = []

        self.scrape_interval = ace_scrape_settings.scrape_interval
        self.disallowed_words = ace_scrape_settings.disallowed_words

        self._ace_quality = AceQuality(ace_quality_cache_path)

        self.site_list_html = ace_scrape_settings.site_list_html
        self.site_list_iptv_m3u8 = ace_scrape_settings.site_list_iptv_m3u8
        self.run_scrape()
        self.print_streams()

    def run_scrape(self) -> None:
        """Run the scraper to find AceStreams."""
        logger.info("Running AceStream scraper...")

        self.streams.extend(
            scrape_streams_html_sites(
                sites=self.site_list_html,
                disallowed_words=self.disallowed_words,
            )
        )

        self.streams.extend(
            scrape_streams_iptv_sites(
                sites=self.site_list_iptv_m3u8,
                disallowed_words=self.disallowed_words,
            )
        )

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

    def get_streams(self) -> list[FoundAceStreams]:
        """Get the found streams as a list of dicts, ready to be turned into json."""
        streams = list(self.streams)

        for found_stream in streams:
            for stream in found_stream.stream_list:
                stream.quality = self._ace_quality.get_quality(stream.ace_id)

        return streams

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
        msg = "Found AceStreams:\n"
        for found_streams in self.streams:
            n = n + len(found_streams.stream_list)
        logger.info(msg)
