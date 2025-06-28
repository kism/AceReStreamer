"""Scraper object."""

import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from acerestreamer.config.models import AceScrapeConf
from acerestreamer.services.epg import EPGHandler
from acerestreamer.utils.logger import get_logger

from .html import HTTPStreamScraper
from .iptv import IPTVStreamScraper
from .models import AceScraperSourceApi, AceScraperSourcesApi, FlatFoundAceStream, FoundAceStreams
from .name_processor import StreamNameProcessor
from .quality import AceQuality, Quality

if TYPE_CHECKING:
    from acerestreamer.config.models import EPGInstanceConf, ScrapeSiteHTML, ScrapeSiteIPTV
else:
    ScrapeSiteHTML = object
    ScrapeSiteIPTV = object
    EPGInstanceConf = object

logger = get_logger(__name__)

SCRAPE_INTERVAL = 60 * 60  # Default scrape interval in seconds (1 hour)


class AceScraper:
    """Scraper object."""

    # region Initialization
    def __init__(self) -> None:
        """Init the scraper."""
        self.external_url: str = ""
        self.streams: list[FoundAceStreams] = []
        self.html: list[ScrapeSiteHTML] = []
        self.iptv_m3u8: list[ScrapeSiteIPTV] = []
        self._ace_quality = AceQuality()
        self.epg_handler: EPGHandler = EPGHandler()
        self.stream_name_processor: StreamNameProcessor = StreamNameProcessor()
        self.html_scraper: HTTPStreamScraper = HTTPStreamScraper()
        self.iptv_scraper: IPTVStreamScraper = IPTVStreamScraper()

    def load_config(
        self,
        ace_scrape_settings: AceScrapeConf,
        epg_conf_list: list[EPGInstanceConf],
        instance_path: Path | str,
        external_url: str,
    ) -> None:
        """Load the configuration for the scraper."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)

        self.external_url = external_url
        self.epg_handler.load_config(epg_conf_list=epg_conf_list, instance_path=instance_path)
        self.html = ace_scrape_settings.html
        self.iptv_m3u8 = ace_scrape_settings.iptv_m3u8
        self._ace_quality.load_config(instance_path=instance_path, external_url=external_url)
        self.stream_name_processor.load_config(instance_path=instance_path)
        self.html_scraper.load_config(instance_path=instance_path, stream_name_processor=self.stream_name_processor)
        self.iptv_scraper.load_config(instance_path=instance_path, stream_name_processor=self.stream_name_processor)

        self.run_scrape()

    # region Scrape
    def run_scrape(self) -> None:
        """Run the scraper to find AceStreams."""

        def run_scrape_thread() -> None:
            """Thread function to run the scraper."""
            while True:
                logger.info("Running AceStream scraper...")

                new_streams = []

                new_streams.extend(
                    self.html_scraper.scrape_sites(
                        sites=self.html,
                    )
                )

                new_streams.extend(
                    self.iptv_scraper.scrape_iptv_playlists(
                        sites=self.iptv_m3u8,
                    )
                )

                self.streams = new_streams
                self.print_streams()
                self.epg_handler.set_of_tvg_ids = {
                    stream.tvg_id for found_streams in self.streams for stream in found_streams.stream_list
                }
                time.sleep(SCRAPE_INTERVAL)

        threading.Thread(target=run_scrape_thread, name="AceScraper: run_scrape", daemon=True).start()

    # region GET
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
            tvg_id="",
            has_ever_worked=False,
        )

    def get_all_streams_by_source(self) -> list[FoundAceStreams]:
        """Get the found streams as a list of dicts, ready to be turned into json."""
        streams = list(self.streams)

        for found_stream in streams:
            for stream in found_stream.stream_list:
                stream.quality = self._ace_quality.get_quality(stream.ace_id).quality

        return streams

    def get_streams_by_source(self, source_slug: str) -> list[FlatFoundAceStream] | None:
        """Get the found streams for a specific source by its slug."""
        for scraped_streams_listing in self.streams:
            if scraped_streams_listing.site_slug == source_slug:
                return [
                    FlatFoundAceStream(
                        site_name=scraped_streams_listing.site_name,
                        quality=self._ace_quality.get_quality(stream.ace_id).quality,
                        title=stream.title,
                        ace_id=stream.ace_id,
                        tvg_id=stream.tvg_id,
                        has_ever_worked=self._ace_quality.get_quality(stream.ace_id).has_ever_worked,
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
                    quality=self._ace_quality.get_quality(stream["ace_id"]).quality,
                    has_ever_worked=self._ace_quality.get_quality(stream["ace_id"]).has_ever_worked,
                    title=stream["title"],
                    ace_id=stream["ace_id"],
                    tvg_id=stream["tvg_id"],
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

    def get_streams_health(self) -> dict[str, Quality]:
        """Get the health of the streams."""
        return self._ace_quality.ace_streams

    # region Quality
    def increment_quality(self, ace_id: str, rating: int) -> None:
        """Increment the quality of a stream by ace_id."""
        self._ace_quality.increment_quality(ace_id, rating)

    def check_missing_quality(self) -> bool:
        """Check the quality of all streams."""
        if self._ace_quality.currently_checking_quality:
            return False

        self._ace_quality.check_missing_quality()

        return True

    # region Helpers
    def print_streams(self) -> None:
        """Print the found streams."""
        if not self.streams:
            logger.warning("Scraper found no AceStreams.")
            return

        # Collect all unique ace_ids
        unique_ace_ids = set()
        for found_streams in self.streams:
            for stream in found_streams.stream_list:
                unique_ace_ids.add(stream.ace_id)

        n = len(unique_ace_ids)
        msg = f"Found AceStreams: {n} unique streams across {len(self.streams)} site definitions."
        logger.info(msg)

    def get_streams_as_iptv(self) -> str:
        """Get the found streams as an IPTV M3U8 string."""
        if not self.external_url:
            logger.error("External URL is not set, cannot generate IPTV streams.")
            return ""

        hls_path = self.external_url + "/hls/"

        return self.stream_name_processor.get_streams_as_iptv(
            streams=self.get_streams_flat(),
            hls_path=hls_path,
        )
