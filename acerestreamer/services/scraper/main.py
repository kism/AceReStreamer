"""Scraper object."""

import contextlib
import json
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

import requests

from acerestreamer.services.epg import EPGHandler
from acerestreamer.utils.logger import get_logger

from .html import HTTPStreamScraper
from .iptv import IPTVStreamScraper
from .models import AceScraperSourceApi, AceScraperSourcesApi, FlatFoundAceStream
from .name_processor import StreamNameProcessor
from .quality import AceQuality

if TYPE_CHECKING:
    from acerestreamer.config.models import AceScrapeConf, EPGInstanceConf, ScrapeSiteHTML, ScrapeSiteIPTV

    from .models import FoundAceStreams
    from .quality import Quality
else:
    ScrapeSiteHTML = object
    ScrapeSiteIPTV = object
    EPGInstanceConf = object
    AceScrapeConf = object
    FoundAceStreams = object
    Quality = object

logger = get_logger(__name__)

SCRAPE_INTERVAL = 60 * 60  # Default scrape interval in seconds (1 hour)


class AceScraper:
    """Scraper object."""

    # region Initialization
    def __init__(self) -> None:
        """Init the scraper."""
        self.external_url: str = ""
        self.ace_url: str = ""
        self.streams: list[FoundAceStreams] = []
        self.html: list[ScrapeSiteHTML] = []
        self.iptv_m3u8: list[ScrapeSiteIPTV] = []
        self._ace_quality = AceQuality()
        self.epg_handler: EPGHandler = EPGHandler()
        self.stream_name_processor: StreamNameProcessor = StreamNameProcessor()
        self.html_scraper: HTTPStreamScraper = HTTPStreamScraper()
        self.iptv_scraper: IPTVStreamScraper = IPTVStreamScraper()
        self.currently_checking_quality: bool = False
        self.instance_path: Path | None = None

    def load_config(
        self,
        ace_scrape_settings: AceScrapeConf,
        epg_conf_list: list[EPGInstanceConf],
        instance_path: Path | str,
        external_url: str,
        ace_url: str,
    ) -> None:
        """Load the configuration for the scraper."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)

        self.instance_path = instance_path
        self.external_url = external_url
        self.ace_url = ace_url
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
                self.populate_missing_content_ids()
                time.sleep(SCRAPE_INTERVAL)

        threading.Thread(target=run_scrape_thread, name="AceScraper: run_scrape", daemon=True).start()

    # region GET
    def get_stream_by_ace_content_id(self, ace_content_id: str) -> FlatFoundAceStream:
        """Get a stream by its Ace ID, will use the first found matching FlatFoundAceStream by ace_content_id."""
        streams = self.get_streams_flat()
        for found_stream in streams:
            if found_stream.ace_content_id == ace_content_id:
                return found_stream

        return FlatFoundAceStream(  # Default return if no stream is found
            site_name="Unknown",
            quality=self._ace_quality.default_quality,
            title=ace_content_id,
            ace_content_id=ace_content_id,
            ace_infohash="",
            tvg_id="",
            tvg_logo="",
            has_ever_worked=False,
        )

    def get_all_streams_by_source(self) -> list[FoundAceStreams]:
        """Get the found streams as a list of dicts, ready to be turned into json."""
        streams = list(self.streams)

        for found_stream in streams:
            for stream in found_stream.stream_list:
                stream.quality = self._ace_quality.get_quality(stream.ace_content_id).quality

        return streams

    def get_streams_by_source(self, source_slug: str) -> list[FlatFoundAceStream] | None:
        """Get the found streams for a specific source by its slug."""
        for scraped_streams_listing in self.streams:
            if scraped_streams_listing.site_slug == source_slug:
                shortlist = []

                for stream in scraped_streams_listing.stream_list:
                    new_stream = FlatFoundAceStream(
                        site_name=scraped_streams_listing.site_name,
                        quality=self._ace_quality.get_quality(stream.ace_content_id).quality,
                        title=stream.title,
                        ace_content_id=stream.ace_content_id,
                        ace_infohash=stream.ace_infohash,
                        tvg_id=stream.tvg_id,
                        tvg_logo=stream.tvg_logo,
                        has_ever_worked=self._ace_quality.get_quality(stream.ace_content_id).has_ever_worked,
                    )

                    program_title, program_description = self.epg_handler.get_current_program(tvg_id=stream.tvg_id)
                    new_stream.program_title = program_title
                    new_stream.program_description = program_description

                    shortlist.append(new_stream)

                return shortlist

        logger.warning("No scraper source found with slug: %s", source_slug)
        return None

    def get_streams_flat(self) -> list[FlatFoundAceStream]:
        """Get a list of streams, as a list of dicts."""
        streams = [stream.model_dump() for stream in self.streams]

        flat_streams: list[FlatFoundAceStream] = []
        for found_stream in streams:
            for stream in found_stream["stream_list"]:
                program_title, program_description = self.epg_handler.get_current_program(tvg_id=stream["tvg_id"])

                new_stream: FlatFoundAceStream = FlatFoundAceStream(
                    site_name=found_stream["site_name"],
                    quality=self._ace_quality.get_quality(stream["ace_content_id"]).quality,
                    has_ever_worked=self._ace_quality.get_quality(stream["ace_content_id"]).has_ever_worked,
                    title=stream["title"],
                    ace_content_id=stream["ace_content_id"],
                    ace_infohash=stream["ace_infohash"],
                    tvg_id=stream["tvg_id"],
                    tvg_logo=stream["tvg_logo"],
                    program_title=program_title,
                    program_description=program_description,
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
    def increment_quality(self, ace_content_id: str, m3u_playlist: str = "") -> None:
        """Increment the quality of a stream by ace_content_id."""
        self._ace_quality.increment_quality(ace_content_id=ace_content_id, m3u_playlist=m3u_playlist)

    def check_missing_quality(self) -> bool:
        """Check the quality of all streams."""
        if self.currently_checking_quality:
            return False

        def check_missing_quality_thread(base_url: str) -> None:
            self.currently_checking_quality = True

            streams = self.get_streams_flat()
            if not streams:
                logger.warning("No streams found to check quality.")
                self.currently_checking_quality = False
                return

            ace_streams_never_worked = len(
                [  # We also check if the quality is zero, since maybe it started working
                    ace_content_id for ace_content_id, _ in self._ace_quality.ace_streams.items()
                ]
            )

            # We only iterate through streams from get_streams_flat()
            # since we don't want to health check streams that are not current per the scraper.
            # Don't enumerate here, and don't bother with list comprehension tbh
            n = 0
            for stream in streams:
                if not stream.has_ever_worked or stream.quality == 0:
                    n += 1
                    stream_url = f"{base_url}/{stream.ace_content_id}"
                    logger.info("Checking Ace Stream %s (%d/%d)", stream_url, n, ace_streams_never_worked)

                    for _ in range(3):
                        with contextlib.suppress(requests.Timeout, requests.ConnectionError):
                            requests.get(stream_url, timeout=10)
                        time.sleep(1)

                    time.sleep(10)

            self.currently_checking_quality = False

        url = f"{self.external_url}/hls"

        thread = threading.Thread(
            target=check_missing_quality_thread,
            name="AceQuality: check_missing_quality",
            args=(url,),
            daemon=True,
        )
        thread.start()

        return True

    # region Helpers
    def print_streams(self) -> None:
        """Print the found streams."""
        if not self.streams:
            logger.warning("Scraper found no AceStreams.")
            return

        # Collect all unique ace_content_ids
        unique_ace_content_ids = set()
        for found_streams in self.streams:
            for stream in found_streams.stream_list:
                unique_ace_content_ids.add(stream.ace_content_id)

        n = len(unique_ace_content_ids)
        msg = f"Found AceStreams: {n} unique streams across {len(self.streams)} site definitions."
        logger.info(msg)

    def get_streams_as_iptv(self) -> str:
        """Get the found streams as an IPTV M3U8 string."""
        if not self.external_url:
            logger.error("External URL is not set, cannot generate IPTV streams.")
            return ""

        external_url = self.external_url

        return self.stream_name_processor.get_streams_as_iptv(
            streams=self.get_streams_flat(),
            external_url=external_url,
        )

    def populate_missing_content_ids(self) -> None:
        """Populate missing content IDs for streams that have an infohash."""
        if not self.instance_path:
            return

        url = f"{self.ace_url}/server/api?api_version=3&method=get_content_id&infohash="

        content_id_infohash_map: dict[str, str] = {}

        content_id_infohash_map_file = self.instance_path / "content_id_infohash_map.json"
        if content_id_infohash_map_file.exists():
            try:
                with content_id_infohash_map_file.open("r", encoding="utf-8") as file:
                    content_id_infohash_map = json.load(file)
            except (json.JSONDecodeError, OSError):
                pass

        for found_streams in self.streams:
            for stream in found_streams.stream_list:
                if not stream.ace_content_id:
                    stream.ace_content_id = content_id_infohash_map.get(stream.ace_infohash, "")

        for found_streams in self.streams:
            for stream in found_streams.stream_list:
                if not stream.ace_content_id and stream.ace_infohash:
                    try:
                        resp = requests.get(
                            f"{url}{stream.ace_infohash}",
                            timeout=10,
                        )
                        resp.raise_for_status()
                        data = resp.json()
                    except (requests.RequestException, ValueError):
                        logger.error(  # noqa: TRY400 Short error for requests
                            "Failed to fetch content ID for stream %s with infohash %s",
                            stream.title,
                            stream.ace_infohash,
                        )
                        continue

                    if data.get("result", {}).get("content_id"):
                        stream.ace_content_id = data["result"]["content_id"]
                        logger.info(
                            "Populated missing content ID for stream %s: %s",
                            stream.title,
                            stream.ace_content_id,
                        )
                        content_id_infohash_map[stream.ace_infohash] = stream.ace_content_id

        with content_id_infohash_map_file.open("w", encoding="utf-8") as file:
            json.dump(content_id_infohash_map, file, indent=4)
