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
from acerestreamer.utils.xc import XCStream, content_id_xc_id_mapping

from .helpers import create_unique_stream_list
from .html import HTTPStreamScraper
from .iptv import IPTVStreamScraper
from .models import AceScraperSourceApi, FoundAceStream, FoundAceStreamAPI
from .name_processor import StreamNameProcessor
from .quality import AceQuality

if TYPE_CHECKING:
    from acerestreamer.config.models import AceScrapeConf, EPGInstanceConf, ScrapeSiteHTML, ScrapeSiteIPTV

    from .quality import Quality
else:
    ScrapeSiteHTML = object
    ScrapeSiteIPTV = object
    EPGInstanceConf = object
    AceScrapeConf = object
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
        self.streams: dict[str, FoundAceStream] = {}
        self.html: list[ScrapeSiteHTML] = []
        self.iptv_m3u8: list[ScrapeSiteIPTV] = []
        self._ace_quality = AceQuality()
        self.epg_handler: EPGHandler = EPGHandler()
        self.stream_name_processor: StreamNameProcessor = StreamNameProcessor()
        self.html_scraper: HTTPStreamScraper = HTTPStreamScraper()
        self.iptv_scraper: IPTVStreamScraper = IPTVStreamScraper()
        self.currently_checking_quality: bool = False

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

        self._run_scrape()

    # region Scrape
    def _run_scrape(self) -> None:
        """Run the scraper to find AceStreams."""

        def run_scrape_thread() -> None:
            """Thread function to run the scraper."""
            while True:
                logger.info("Running AceStream scraper")

                found_html_streams = self.html_scraper.scrape_sites(sites=self.html)
                found_iptv_streams = self.iptv_scraper.scrape_iptv_playlists(sites=self.iptv_m3u8)

                found_streams = found_html_streams + found_iptv_streams

                self.streams = create_unique_stream_list(found_streams)
                self._populate_infohashes()

                # Populate ourself
                self._print_streams()

                # EPGs
                tvg_id_list = [stream.tvg_id for stream in self.streams.values()]
                self.epg_handler.add_tvg_ids(tvg_ids=tvg_id_list)

                # For streams with only an infohash, populate the content_id using the api
                for _ in range(2):
                    missing_content_id_streams = [
                        stream for stream in found_streams if not stream.content_id and stream.infohash
                    ]
                    if len(missing_content_id_streams) == 0:
                        break

                    newly_populated_streams = self._populate_missing_content_ids(missing_content_id_streams)
                    if len(newly_populated_streams) != 0:
                        self.streams = create_unique_stream_list(list(self.streams.values()) + newly_populated_streams)
                    time.sleep(60)

                time.sleep(SCRAPE_INTERVAL)

        threading.Thread(target=run_scrape_thread, name="AceScraper: run_scrape", daemon=True).start()

    # region GET API
    def get_stream_by_content_id_api(self, content_id: str) -> FoundAceStreamAPI:
        """Get a stream by its Ace ID, will use the first found matching FoundAceStreamAPI by content_id."""
        if content_id in self.streams:
            stream = self.streams[content_id]
            program_title, program_description = self.epg_handler.get_current_program(tvg_id=stream.tvg_id)

            return FoundAceStreamAPI(
                site_names=stream.site_names,
                quality=self._ace_quality.get_quality(content_id).quality,
                has_ever_worked=self._ace_quality.get_quality(content_id).has_ever_worked,
                title=stream.title,
                content_id=stream.content_id,
                infohash=stream.infohash,
                tvg_id=stream.tvg_id,
                tvg_logo=stream.tvg_logo,
                program_title=program_title,
                program_description=program_description,
            )

        return FoundAceStreamAPI(  # Default return if no stream is found
            site_names=["Unknown"],
            quality=self._ace_quality.default_quality,
            title=content_id,
            content_id=content_id,
            infohash="",
            tvg_id="",
            tvg_logo="",
            has_ever_worked=False,
        )

    def get_stream_list_api(self) -> list[FoundAceStreamAPI]:
        """Get a list of streams, as a list of dicts, deduplicated by content_id."""
        return [self.get_stream_by_content_id_api(content_id=content_id) for content_id in self.streams]

    # region GET API Scraper
    def get_scraper_sources_flat_api(self) -> list[AceScraperSourceApi]:
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

    def get_content_id_by_xc_id(self, xc_id: int) -> str | None:
        """Get the content ID by XC ID."""
        return content_id_xc_id_mapping.get_content_id(xc_id=xc_id)

    # region GET IPTV
    def get_streams_as_iptv(self) -> str:
        """Get the found streams as an IPTV M3U8 string."""
        if not self.external_url:
            logger.error("External URL is not set, cannot generate IPTV streams.")
            return ""

        # There are a few standards for the tag for the tvg url, most to least common x-tvg-url, url-tvg, tvg-url
        epg_url = f"{self.external_url}/epg"
        m3u8_content = f'#EXTM3U x-tvg-url="{epg_url}" url-tvg="{epg_url}" refresh="3600"\n'

        iptv_set = set()

        # I used to filter this for whether the stream has ever worked,
        # but sometimes sites change the id of their stream often...
        for stream in self.streams.values():
            logger.debug(stream)

            # Country codes are 2 characters between square brackets, e.g. [US]
            tvg_id = f'tvg-id="{stream.tvg_id}"'
            tvg_logo = f'tvg-logo="{self.external_url}/tvg-logo/{stream.tvg_logo}"' if stream.tvg_logo else ""
            group_category = f'group-title="{stream.group_title}"'

            m3u8_addition = (
                f"#EXTINF:-1 {tvg_id} {tvg_logo} {group_category},{stream.title}\n"
                f"{self.external_url}/hls/{stream.content_id}"
            )

            iptv_set.add(m3u8_addition)

        return m3u8_content + "\n".join(sorted(iptv_set))

    def get_streams_as_iptv_xc(self) -> list[XCStream]:
        """Get the found streams as a list of XCStream objects."""
        streams: list[XCStream] = []

        current_stream_number = 1
        for stream in self.streams.values():
            xc_id = content_id_xc_id_mapping.get_xc_id(stream.content_id)
            streams.append(
                XCStream(
                    num=current_stream_number,
                    name=stream.title,
                    stream_id=xc_id,
                    stream_icon=f"{self.external_url}/tvg-logo/{stream.tvg_logo}" if stream.tvg_logo else "",
                    epg_channel_id=stream.tvg_id,
                )
            )
            current_stream_number += 1

        return streams

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

            streams = self.get_stream_list_api()  # API method gets teh health information
            if not streams:
                logger.warning("No streams found to check quality.")
                self.currently_checking_quality = False
                return

            ace_streams_never_worked = len(
                [  # We also check if the quality is zero, since maybe it started working
                    content_id for content_id, _ in self._ace_quality.ace_streams.items()
                ]
            )

            # We only iterate through streams from get_stream_list_api()
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
    def _print_streams(self) -> None:
        """Print the found streams."""
        if not self.streams:
            logger.warning("Scraper found no AceStreams.")
            return

        n = len(self.streams)
        msg = f"Found AceStreams: {n} unique streams across {len(self.streams)} site definitions."
        logger.info(msg)

    def _populate_infohashes(self) -> None:
        """Populate infohashes for streams that have a content ID."""
        for stream in self.streams.values():
            if not stream.infohash:
                stream.infohash = content_id_infohash_mapping.get_infohash(
                    content_id=stream.content_id,
                )

    def _populate_missing_content_ids(self, streams: list[FoundAceStream]) -> list[FoundAceStream]:
        """Populate missing content IDs for streams that have an infohash."""
        populated_streams: list[FoundAceStream] = []

        for stream in streams:
            if not stream.content_id:
                stream.content_id = content_id_infohash_mapping.get_content_id(
                    infohash=stream.infohash,
                )
                if stream.content_id:
                    populated_streams.append(stream)

        for stream in streams:
            if not stream.content_id:
                stream.content_id = content_id_infohash_mapping.populate_from_api(
                    infohash=stream.infohash,
                )
                if not stream.content_id:
                    logger.error(
                        "Failed to populate content ID for stream with infohash %s, skipping",
                        stream.infohash,
                    )
                else:
                    populated_streams.append(stream)

        return populated_streams
