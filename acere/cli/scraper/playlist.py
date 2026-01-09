"""Object for adhoc playlist creation."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import HttpUrl

from acere.core.config import AceReStreamerConf, ScrapeSiteIPTV
from acere.services.scraper import (
    APIStreamScraper,
    FoundAceStream,
    HTMLStreamScraper,
    IPTVStreamScraper,
    StreamNameProcessor,
    create_unique_stream_list,
)
from acere.services.scraper.helpers import create_extinf_line
from acere.utils.logger import get_logger

from .constants import M3U_URI_SCHEMES

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object

logger = get_logger(__name__)


class PlaylistCreator:
    """Class to generate playlists."""

    def __init__(self, instance_path: Path, config: AceReStreamerConf) -> None:
        """Initialize the PlaylistCreator."""
        self._instance_path = instance_path
        self._conf = config
        self.playlist_name = config.scraper.playlist_name
        self._output_directory = self._instance_path / "playlists"
        self._output_directory.mkdir(parents=True, exist_ok=True)
        self._html_scraper = HTMLStreamScraper()
        self._iptv_scraper = IPTVStreamScraper()
        self._api_scraper = APIStreamScraper()

        stream_name_processor = StreamNameProcessor()

        stream_name_processor.load_config(
            instance_path=self._instance_path,
            name_replacements=self._conf.scraper.name_replacements,
            category_mapping=self._conf.scraper.category_mapping,
        )
        self._html_scraper.load_config(
            instance_path=self._instance_path,
            stream_name_processor=stream_name_processor,
            adhoc_mode=True,
        )
        self._iptv_scraper.load_config(
            instance_path=self._instance_path,
            stream_name_processor=stream_name_processor,
            adhoc_mode=True,
        )
        self._api_scraper.load_config(
            instance_path=self._instance_path,
            stream_name_processor=stream_name_processor,
            adhoc_mode=True,
        )

    async def scrape(self) -> None:
        """Scrape the streams."""
        found_streams: list[FoundAceStream] = await self._scrape_remote()
        await self._create_playlist(streams=found_streams)

    async def _scrape_remote(self) -> list[FoundAceStream]:
        found_html_streams = await self._html_scraper.scrape_sites(sites=self._conf.scraper.html)
        found_iptv_streams = await self._iptv_scraper.scrape_iptv_playlists(sites=self._conf.scraper.iptv_m3u8)
        found_api_streams = await self._api_scraper.scrape_api_endpoints(sites=self._conf.scraper.api)
        logger.info(
            "Scraper has found streams: %d from HTML, %d from IPTV, %d from API",
            len(found_html_streams),
            len(found_iptv_streams),
            len(found_api_streams),
        )
        found_streams = found_html_streams + found_iptv_streams + found_api_streams
        found_streams_unique = list(create_unique_stream_list(found_streams).values())  # Unique list of content_ids
        found_streams_infohash_only = [stream for stream in found_streams if stream.infohash and not stream.content_id]
        return found_streams_unique + found_streams_infohash_only

    async def _scrape_existing(self) -> list[FoundAceStream]:
        content_id_results = []
        infohash_results = []

        ace_playlist_content_id = self._output_directory / f"{self.playlist_name}-ace.m3u"
        site = ScrapeSiteIPTV(
            name=ace_playlist_content_id.stem,
            url=HttpUrl(f"https://localhost/{ace_playlist_content_id.name}"),
        )
        if ace_playlist_content_id.exists():
            with ace_playlist_content_id.open("r", encoding="utf-8") as m3u_file:
                content = m3u_file.read()
                content_id_results = await self._iptv_scraper.parse_m3u_content(content=content, site=site)

        ace_playlist_infohash = self._output_directory / f"{self.playlist_name}-local-infohash.m3u"
        site = ScrapeSiteIPTV(
            name=ace_playlist_infohash.stem,
            url=HttpUrl(f"https://localhost/{ace_playlist_infohash.name}"),
        )
        if ace_playlist_infohash.exists():
            with ace_playlist_infohash.open("r", encoding="utf-8") as m3u_file:
                content = m3u_file.read()
                infohash_results = await self._iptv_scraper.parse_m3u_content(content=content, site=site)

        return content_id_results + infohash_results

    async def _create_playlist(self, streams: list[FoundAceStream]) -> None:
        existing_streams = await self._scrape_existing()
        existing_content_id: list[str] = [stream.content_id for stream in existing_streams if stream.content_id != ""]
        existing_infohash: list[str] = [stream.infohash for stream in existing_streams if stream.infohash != ""]

        streams_to_append: list[FoundAceStream] = []

        # Find any streams that were missed...
        for stream in existing_streams:
            if stream.content_id != "" and stream.content_id not in existing_content_id:
                stream.last_found_time = int(datetime.now(tz=UTC).timestamp())
                streams_to_append.append(stream)
            if stream.infohash != "" and stream.infohash not in existing_infohash:
                stream.last_found_time = int(datetime.now(tz=UTC).timestamp())
                streams_to_append.append(stream)

        streams.extend(streams_to_append)
        streams.sort(key=lambda x: x.title.lower())

        infohash_scheme = "infohash-main"
        if infohash_scheme not in M3U_URI_SCHEMES:
            logger.error("Infohash URI scheme not found in M3U_URI_SCHEMES, the developer needs to fix this.")
            return

        for uri_scheme, prefix in M3U_URI_SCHEMES.items():
            playlist_path = self._output_directory / f"{self.playlist_name}-{uri_scheme}.m3u"
            with playlist_path.open("w", encoding="utf-8") as m3u_file:
                epg_urls = [epg.url for epg in self._conf.epgs]
                epg_str = ""
                if epg_urls:
                    epg_str = f'x-tvg-url="{",".join(epg_url.encoded_string() for epg_url in epg_urls)}"'

                m3u_file.write(f"#EXTM3U {epg_str}\n")
                for stream in streams:
                    top_line = create_extinf_line(stream, tvg_url_base=self._conf.scraper.tvg_logo_external_url)
                    if stream.infohash != "" and uri_scheme == infohash_scheme:
                        m3u_file.write(top_line)
                        m3u_file.write(f"{prefix}{stream.infohash}\n")
                    elif stream.content_id != "" and uri_scheme != infohash_scheme:
                        m3u_file.write(top_line)
                        m3u_file.write(f"{prefix}{stream.content_id}\n")
