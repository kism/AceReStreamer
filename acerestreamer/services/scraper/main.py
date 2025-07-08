"""Scraper object."""

import contextlib
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

import requests

from acerestreamer.services.epg import EPGHandler
from acerestreamer.utils.content_id_infohash_mapping import content_id_infohash_mapping
from acerestreamer.utils.logger import get_logger
from acerestreamer.utils.xc import XCStream

from .html import HTTPStreamScraper
from .iptv import IPTVStreamScraper
from .models import AceScraperSourceApi, FlatFoundAceStream
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
        self._missing_quality: bool = False

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
                logger.info("Running AceStream scraper")

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

                # Populate ourself
                self.streams = new_streams
                self.print_streams()

                # EPGs
                tvg_id_list = [stream.tvg_id for found_streams in self.streams for stream in found_streams.stream_list]
                self.epg_handler.add_tvg_ids(tvg_ids=tvg_id_list)

                # For streams with only an infohash, populate the content_id using the api
                self.populate_missing_content_ids()

                if self._missing_quality:
                    time.sleep(60)
                    self.populate_missing_content_ids()

                time.sleep(SCRAPE_INTERVAL)

        threading.Thread(target=run_scrape_thread, name="AceScraper: run_scrape", daemon=True).start()

    # region Getters
    def get_all_streams_by_source(self) -> list[FoundAceStreams]:
        """Get the found streams as a list of dicts, ready to be turned into json."""
        streams = list(self.streams)

        for found_stream in streams:
            for stream in found_stream.stream_list:
                stream.quality = self._ace_quality.get_quality(stream.content_id).quality

        return streams

    # region GET API
    def get_stream_by_content_id_api(self, content_id: str) -> FlatFoundAceStream:
        """Get a stream by its Ace ID, will use the first found matching FlatFoundAceStream by content_id."""
        streams = self.get_streams_flat()
        for found_stream in streams:
            if found_stream.content_id == content_id:
                return found_stream

        return FlatFoundAceStream(  # Default return if no stream is found
            site_names=["Unknown"],
            quality=self._ace_quality.default_quality,
            title=content_id,
            content_id=content_id,
            infohash="",
            tvg_id="",
            tvg_logo="",
            has_ever_worked=False,
        )

    def get_streams_by_source(self, source_slug: str) -> list[FlatFoundAceStream] | None:
        """Get the found streams for a specific source by its slug."""
        for scraped_streams_listing in self.streams:
            if scraped_streams_listing.site_slug == source_slug:
                shortlist = []

                for stream in scraped_streams_listing.stream_list:
                    new_stream = FlatFoundAceStream(
                        site_names=[scraped_streams_listing.site_name],
                        quality=self._ace_quality.get_quality(stream.content_id).quality,
                        title=stream.title,
                        content_id=stream.content_id,
                        infohash=stream.infohash,
                        tvg_id=stream.tvg_id,
                        tvg_logo=stream.tvg_logo,
                        has_ever_worked=self._ace_quality.get_quality(stream.content_id).has_ever_worked,
                    )

                    program_title, program_description = self.epg_handler.get_current_program(tvg_id=stream.tvg_id)
                    new_stream.program_title = program_title
                    new_stream.program_description = program_description

                    shortlist.append(new_stream)

                return shortlist

        logger.warning("No scraper source found with slug: %s", source_slug)
        return None

    def get_streams_flat(self) -> list[FlatFoundAceStream]:
        """Get a list of streams, as a list of dicts, deduplicated by content_id."""
        streams = [stream.model_dump() for stream in self.streams]

        flat_streams: dict[str, FlatFoundAceStream] = {}
        for found_stream in streams:
            for stream in found_stream["stream_list"]:
                program_title, program_description = self.epg_handler.get_current_program(tvg_id=stream["tvg_id"])

                if stream["content_id"] in flat_streams:
                    # If the stream already exists, we append the site name to the existing one
                    existing_stream = flat_streams[stream["content_id"]]
                    existing_stream.site_names.append(found_stream["site_name"])

                else:
                    new_stream: FlatFoundAceStream = FlatFoundAceStream(
                        site_names=[found_stream["site_name"]],
                        quality=self._ace_quality.get_quality(stream["content_id"]).quality,
                        has_ever_worked=self._ace_quality.get_quality(stream["content_id"]).has_ever_worked,
                        title=stream["title"],
                        content_id=stream["content_id"],
                        infohash=stream["infohash"],
                        tvg_id=stream["tvg_id"],
                        tvg_logo=stream["tvg_logo"],
                        program_title=program_title,
                        program_description=program_description,
                    )
                    flat_streams[stream["content_id"]] = new_stream

        return list(flat_streams.values())

    def get_scraper_sources_flat(self) -> list[AceScraperSourceApi]:
        """Get the sources for the scraper, as a flat list."""
        sources = [
            AceScraperSourceApi(
                name=site.name,
                slug=site.slug,
                url=site.url,
                title_filter=site.title_filter,
                type="html",
                check_sibling=site.check_sibling,
                target_class=site.target_class,
            )
            for site in self.html
        ]

        sources.extend(
            [
                AceScraperSourceApi(
                    name=site.name, slug=site.slug, url=site.url, title_filter=site.title_filter, type="iptv"
                )
                for site in self.iptv_m3u8
            ]
        )

        return sources

    def get_streams_health(self) -> dict[str, Quality]:
        """Get the health of the streams."""
        return self._ace_quality.ace_streams

    # region GET IPTV

    def _get_streams_as_iptv(self, streams: list[FlatFoundAceStream], external_url: str) -> str:
        """Get the found streams as an IPTV M3U8 string."""
        m3u8_content = f'#EXTM3U url-tvg="{external_url}/epg"\n'

        iptv_set = set()

        # I used to filter this for whether the stream has ever worked,
        # but sometimes sites change the id of their stream often...
        for stream in streams:
            logger.debug(stream)

            # Country codes are 2 characters between square brackets, e.g. [US]
            tvg_id = f'tvg-id="{stream.tvg_id}"'
            tvg_logo = f'tvg-logo="{external_url}/tvg-logo/{stream.tvg_logo}"' if stream.tvg_logo else ""

            m3u8_addition = f"#EXTINF:-1 {tvg_id} {tvg_logo},{stream.title}\n{external_url}/hls/{stream.content_id}"

            iptv_set.add(m3u8_addition)

        return m3u8_content + "\n".join(sorted(iptv_set))

    def get_streams_as_iptv(self) -> str:
        """Get the found streams as an IPTV M3U8 string."""
        if not self.external_url:
            logger.error("External URL is not set, cannot generate IPTV streams.")
            return ""

        external_url = self.external_url

        return self._get_streams_as_iptv(
            streams=self.get_streams_flat(),
            external_url=external_url,
        )

    def get_streams_as_iptv_xc(self) -> list[XCStream]:
        """Get the found streams as a list of XCStream objects."""
        pass

    # region Quality
    def increment_quality(self, content_id: str, m3u_playlist: str = "") -> None:
        """Increment the quality of a stream by content_id."""
        self._ace_quality.increment_quality(content_id=content_id, m3u_playlist=m3u_playlist)

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
                    content_id for content_id, _ in self._ace_quality.ace_streams.items()
                ]
            )

            # We only iterate through streams from get_streams_flat()
            # since we don't want to health check streams that are not current per the scraper.
            # Don't enumerate here, and don't bother with list comprehension tbh
            n = 0
            for stream in streams:
                if not stream.has_ever_worked or stream.quality == 0:
                    n += 1
                    stream_url = f"{base_url}/{stream.content_id}"
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

        # Collect all unique content_ids
        unique_content_ids = set()
        for found_streams in self.streams:
            for stream in found_streams.stream_list:
                unique_content_ids.add(stream.content_id)

        n = len(unique_content_ids)
        msg = f"Found AceStreams: {n} unique streams across {len(self.streams)} site definitions."
        logger.info(msg)

    def populate_missing_content_ids(self) -> None:
        """Populate missing content IDs for streams that have an infohash."""
        self._missing_quality = False  # Reset the flag

        for found_streams in self.streams:
            for stream in found_streams.stream_list:
                if not stream.content_id:
                    stream.content_id = content_id_infohash_mapping.get_content_id(
                        infohash=stream.infohash,
                    )
                elif not stream.infohash:
                    stream.infohash = content_id_infohash_mapping.get_infohash(
                        content_id=stream.content_id,
                    )

        for found_streams in self.streams:
            for stream in found_streams.stream_list:
                if not stream.content_id and stream.infohash:
                    stream.content_id = content_id_infohash_mapping.populate_from_api(
                        infohash=stream.infohash,
                    )
                    if stream.content_id == "":
                        self._missing_quality = True
