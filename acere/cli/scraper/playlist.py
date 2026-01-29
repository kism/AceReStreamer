"""Object for adhoc playlist creation."""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, cast

from pydantic import HttpUrl

from acere.constants import PLAYLISTS_DIR
from acere.core.config.scraper import ScrapeSiteIPTV
from acere.instances.config import settings
from acere.services.scraper import (
    APIStreamScraper,
    FoundAceStream,
    HTMLStreamScraper,
    IPTVStreamScraper,
    create_unique_stream_list,
)
from acere.utils.logger import get_logger
from acere.utils.m3u8 import create_extinf_line

from .constants import M3U_URI_SCHEMES

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object

logger = get_logger(__name__)

_TIMEDELTA_FRESH = timedelta(minutes=1)
_TIMEDELTA_INVALIDATE_FRESH = _TIMEDELTA_FRESH + timedelta(seconds=1)


class PlaylistCreator:
    """Class to generate playlists."""

    def __init__(self, instance_path: Path) -> None:
        """Initialize the PlaylistCreator."""
        self._instance_path: Path = instance_path
        self._playlists_dir = self._instance_path / PLAYLISTS_DIR.name
        self._playlists_dir.mkdir(parents=True, exist_ok=True)
        self._html_scraper = HTMLStreamScraper(instance_path=instance_path)
        self._iptv_scraper = IPTVStreamScraper(instance_path=instance_path)
        self._api_scraper = APIStreamScraper(instance_path=instance_path)

    async def scrape(self) -> None:
        """Scrape the streams."""
        found_streams: list[FoundAceStream] = await self._scrape_remote()
        await self._create_playlists(new_streams=found_streams)

    async def _scrape_remote(self) -> list[FoundAceStream]:
        tasks = [
            self._html_scraper.scrape_sites(sites=settings.scraper.html),
            self._iptv_scraper.scrape_iptv_playlists(sites=settings.scraper.iptv_m3u8),
            self._api_scraper.scrape_api_endpoints(sites=settings.scraper.api),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        found_html_streams: list[FoundAceStream] = []
        found_iptv_streams: list[FoundAceStream] = []
        found_api_streams: list[FoundAceStream] = []

        if isinstance(results[0], Exception):
            logger.error("Error occurred during HTML scraping: %s", results[0])
        else:
            found_html_streams = cast("list[FoundAceStream]", results[0])

        if isinstance(results[1], Exception):
            logger.error("Error occurred during IPTV scraping: %s", results[1])
        else:
            found_iptv_streams = cast("list[FoundAceStream]", results[1])

        if isinstance(results[2], Exception):
            logger.error("Error occurred during API scraping: %s", results[2])
        else:
            found_api_streams = cast("list[FoundAceStream]", results[2])

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

        ace_playlist_content_id = self._playlists_dir / f"{settings.scraper.playlist_name}-content-id-main.m3u"
        site = ScrapeSiteIPTV(
            name=ace_playlist_content_id.stem,
            url=HttpUrl(f"https://localhost/{ace_playlist_content_id.name}"),
        )
        if ace_playlist_content_id.exists():
            with ace_playlist_content_id.open("r", encoding="utf-8") as m3u_file:
                content = m3u_file.read()
                content_id_results = await self._iptv_scraper.parse_m3u_content(content=content, site=site)
        else:
            logger.debug("Existing ACE playlist not found at %s", ace_playlist_content_id)

        ace_playlist_infohash = self._playlists_dir / f"{settings.scraper.playlist_name}-infohash-main.m3u"
        site = ScrapeSiteIPTV(
            name=ace_playlist_infohash.stem,
            url=HttpUrl(f"https://localhost/{ace_playlist_infohash.name}"),
        )
        if ace_playlist_infohash.exists():
            with ace_playlist_infohash.open("r", encoding="utf-8") as m3u_file:
                content = m3u_file.read()
                infohash_results = await self._iptv_scraper.parse_m3u_content(content=content, site=site)
        else:
            logger.debug("Existing Infohash playlist not found at %s", ace_playlist_infohash)

        combined = content_id_results + infohash_results
        if len(combined) == 0:
            logger.warning("No existing streams found in existing playlists, this is okay for the first run.")
        else:
            logger.info("Loaded %d existing streams from existing playlists", len(combined))

        return content_id_results + infohash_results

    async def _create_playlists(self, new_streams: list[FoundAceStream]) -> None:
        existing_streams = await self._scrape_existing()
        fetched_content_id: list[str] = [stream.content_id for stream in new_streams if stream.content_id != ""]
        fetched_infohash: list[str] = [stream.infohash for stream in new_streams if stream.infohash is not None]

        streams_to_append: list[FoundAceStream] = []

        # Add new streams
        for stream in existing_streams:
            if (stream.content_id != "" and stream.content_id not in fetched_content_id) or (
                stream.infohash is not None and stream.infohash not in fetched_infohash
            ):
                stream.last_scraped_time = datetime.now(tz=UTC) - _TIMEDELTA_INVALIDATE_FRESH
                streams_to_append.append(stream)

        logger.debug("n streams to append: %d", len(streams_to_append))

        streams = new_streams + streams_to_append
        streams.sort(key=lambda x: x.title.lower())

        infohash_scheme = "infohash-main"
        if infohash_scheme not in M3U_URI_SCHEMES:
            logger.error("Infohash URI scheme not found in M3U_URI_SCHEMES, the developer needs to fix this.")
            return

        infohash_streams = len([s for s in streams if s.infohash is not None])
        content_id_streams = len([s for s in streams if s.content_id != ""])
        logger.info(
            "Creating playlists with %d infohash streams and %d content ID streams",
            infohash_streams,
            content_id_streams,
        )

        for uri_scheme, prefix in M3U_URI_SCHEMES.items():
            playlist_path = self._playlists_dir / f"{settings.scraper.playlist_name}-{uri_scheme}.m3u"
            with playlist_path.open("w", encoding="utf-8") as m3u_file:
                epg_urls = [epg.url for epg in settings.epgs]
                epg_str = ""
                if epg_urls:
                    epg_str = f'x-tvg-url="{",".join(epg_url.encoded_string() for epg_url in epg_urls)}"'

                m3u_file.write(f"#EXTM3U {epg_str}\n")
                logger.debug("Creating playlist %s", playlist_path.name)
                for stream in streams:
                    # This logic is for adhoc scraper not chaning playlists unless they are not found recently
                    scraped_within_minute = datetime.now(tz=UTC) - stream.last_scraped_time < _TIMEDELTA_FRESH
                    last_scraped_time = 0 if scraped_within_minute else int(stream.last_scraped_time.timestamp())

                    top_line = create_extinf_line(
                        stream, tvg_url_base=settings.scraper.tvg_logo_external_url, last_found=last_scraped_time
                    )
                    if uri_scheme == infohash_scheme and stream.infohash is not None:
                        m3u_file.write(top_line)
                        m3u_file.write(f"{prefix}{stream.infohash}\n")
                    elif uri_scheme != infohash_scheme and stream.content_id != "":
                        m3u_file.write(top_line)
                        m3u_file.write(f"{prefix}{stream.content_id}\n")
