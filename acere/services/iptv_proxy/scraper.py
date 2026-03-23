"""IPTV proxy scraper — fetches upstream playlists and XC APIs."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import aiohttp

from acere.services.scraper import name_processor
from acere.services.scraper.cache import ScraperCache
from acere.services.scraper.m3u_common import GenericM3UParser, M3UEntry
from acere.services.scraper.models import FoundIPTVStream
from acere.services.xc.models import XCApiResponse, XCCategory, XCStream
from acere.utils.exception_handling import log_aiohttp_exception
from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from pydantic import HttpUrl

    from acere.config.iptv import IPTVSourceM3U8, IPTVSourceXtream
else:
    IPTVSourceM3U8 = object
    IPTVSourceXtream = object
    HttpUrl = object

logger = get_logger(__name__)

IPTV_CACHE_MAX_AGE = timedelta(hours=1)
DEFAULT_HTTP_PORT = 80
DEFAULT_HTTPS_PORT = 443


class IPTVProxyScraper:
    """Scrapes IPTV sources (M3U8 and Xtream Codes) for stream entries."""

    def __init__(self) -> None:
        """Initialize the IPTV proxy scraper."""
        self._generic_parser = GenericM3UParser()
        self._scraper_cache = ScraperCache()

    async def scrape_m3u8_source(self, source: IPTVSourceM3U8) -> list[FoundIPTVStream]:
        """Fetch an M3U8 URL and parse it for IPTV stream entries."""
        content = await self._get_cached_or_fetch(source.url, source.name)
        if not content:
            return []

        entries = self._generic_parser.parse(content)
        return self._filter_and_convert_entries(entries, source.name, source)

    async def scrape_xtream_source(self, source: IPTVSourceXtream) -> list[FoundIPTVStream]:
        """Use XC player_api.php to get streams, then build upstream URLs."""
        base_url = source.url.encoded_string().rstrip("/")

        # Fetch server info to check max_connections
        api_url = f"{base_url}/player_api.php?username={source.username}&password={source.password}"
        api_data = await self._fetch_json(api_url, source.name)
        if api_data is None or not isinstance(api_data, dict):
            return []

        try:
            api_response = XCApiResponse(**api_data)
        except Exception:
            logger.exception("Failed to parse XC API response for source '%s'", source.name)
            return []

        xc_max = int(api_response.user_info.max_connections)
        if source.max_active_streams > 0 and source.max_active_streams > xc_max:
            logger.warning(
                "IPTV source '%s': max_active_streams (%d) exceeds XC max_connections (%d)",
                source.name,
                source.max_active_streams,
                xc_max,
            )

        # Fetch live streams and categories
        streams_raw = await self._fetch_json(f"{api_url}&action=get_live_streams", source.name)
        if streams_raw is None or not isinstance(streams_raw, list):
            logger.error("Failed to fetch live streams for source '%s'", source.name)
            return []

        try:
            streams_data = [XCStream(**s) for s in streams_raw]
        except Exception:
            logger.exception("Failed to parse XC streams for source '%s'", source.name)
            return []

        category_map = await self._fetch_xc_category_map(api_url, source.name)

        # Build the stream base URL from server_info (may differ from the API URL)
        server = api_response.server_info
        if server.server_protocol == "https" and server.https_port:
            port_suffix = "" if server.https_port == DEFAULT_HTTPS_PORT else f":{server.https_port}"
            stream_base_url = f"https://{server.url.host}{port_suffix}"
        else:
            port_suffix = "" if server.port == DEFAULT_HTTP_PORT else f":{server.port}"
            stream_base_url = f"http://{server.url.host}{port_suffix}"

        found_streams = self._build_xc_streams(streams_data, category_map, stream_base_url, source)
        logger.info("Found %d streams from XC source '%s'", len(found_streams), source.name)
        return found_streams

    async def _fetch_xc_category_map(self, api_url: str, source_name: str) -> dict[int, str]:
        """Fetch XC categories and build a category_id -> category_name map."""
        categories_data = await self._fetch_json(f"{api_url}&action=get_live_categories", source_name)
        category_map: dict[int, str] = {}
        if categories_data and isinstance(categories_data, list):
            for cat_data in categories_data:
                try:
                    cat = XCCategory.model_validate(cat_data)
                except Exception:
                    continue
                if cat.category_name:
                    category_map[cat.category_id] = cat.category_name
        return category_map

    def _build_xc_streams(
        self,
        streams_data: list[XCStream],
        category_map: dict[int, str],
        base_url: str,
        source: IPTVSourceXtream,
    ) -> list[FoundIPTVStream]:
        """Build FoundIPTVStream entries from XC stream data."""
        found_streams: list[FoundIPTVStream] = []
        now = datetime.now(tz=UTC)

        for stream in streams_data:
            title = stream.name.strip()
            if not title:
                continue

            group_title = category_map.get(stream.category_id, "") or "General"

            # Apply category filter
            if not source.category_filter.check_allowed(group_title, thing_were_checking="Category"):
                continue

            group_title = source.category_rename.get(group_title, group_title)

            if not source.title_filter.check_allowed(title):
                continue

            # Apply per-stream overrides
            override = source.stream_overrides.get(title)
            if override:
                if override.name:
                    title = override.name
                if override.category:
                    group_title = override.category
                tvg_id = override.tvg_id or stream.epg_channel_id
            else:
                tvg_id = stream.epg_channel_id

            # Build upstream URL
            upstream_url = f"{base_url}/live/{source.username}/{source.password}/{stream.stream_id}.m3u8"

            found_streams.append(
                FoundIPTVStream(
                    title=title,
                    upstream_url=upstream_url,
                    source_name=source.name,
                    tvg_id=tvg_id,
                    tvg_logo=stream.stream_icon or None,
                    group_title=group_title,
                    last_scraped_time=now,
                )
            )

        return found_streams

    def _filter_and_convert_entries(
        self,
        entries: list[M3UEntry],
        source_name: str,
        source: IPTVSourceM3U8 | IPTVSourceXtream,
    ) -> list[FoundIPTVStream]:
        """Apply title and category filters, convert M3UEntry to FoundIPTVStream."""
        results: list[FoundIPTVStream] = []
        now = datetime.now(tz=UTC)

        for entry in entries:
            # Skip non-HTTP URLs (ace streams, etc.)
            if not entry.url.startswith("http"):
                continue

            title = entry.title.strip()

            # Apply title filter
            if not source.title_filter.check_allowed(title):
                continue

            group_title = entry.group_title or "General"

            # Apply category filter
            if not source.category_filter.check_allowed(group_title, thing_were_checking="Category"):
                continue

            group_title = source.category_rename.get(group_title, group_title)

            # Apply per-stream overrides
            override = source.stream_overrides.get(title)
            if override:
                if override.name:
                    title = override.name
                if override.category:
                    group_title = override.category
                tvg_id = override.tvg_id or entry.tvg_id
            else:
                tvg_id = entry.tvg_id

            results.append(
                FoundIPTVStream(
                    title=title,
                    upstream_url=entry.url,
                    source_name=source_name,
                    tvg_id=tvg_id,
                    tvg_logo=None,  # TVG logo handling for IPTV proxy is separate
                    group_title=group_title,
                    last_scraped_time=now,
                )
            )

        logger.info("Found %d IPTV streams from M3U8 source '%s'", len(results), source_name)
        return results

    async def _get_cached_or_fetch(self, url: HttpUrl, source_name: str) -> str | None:
        """Get content from cache or fetch from URL."""
        if self._scraper_cache.is_cache_valid(url, cache_max_age=IPTV_CACHE_MAX_AGE):
            logger.debug("Loaded IPTV source content from cache for: %s", source_name)
            return self._scraper_cache.load_from_cache(url)

        logger.info("Fetching IPTV source: %s", source_name)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url.encoded_string()) as response:
                    response.raise_for_status()
                    content = await response.text(encoding="utf-8")
        except (aiohttp.ClientError, TimeoutError) as e:
            log_aiohttp_exception(logger, url, e)
            return None

        self._scraper_cache.save_to_cache(url, content)
        return content

    async def _fetch_json(self, url: str, source_name: str) -> Any:  # noqa: ANN401
        """Fetch JSON from a URL."""
        logger.debug("Fetching JSON from %s for source '%s'", url, source_name)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as e:
            log_aiohttp_exception(logger, url, e)
            return None
