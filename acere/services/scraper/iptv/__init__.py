"""Scraper for IPTV sites to find AceStream streams."""

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import aiohttp
from pydantic import HttpUrl

from acere.constants import SUPPORTED_TVG_LOGO_EXTENSIONS
from acere.instances.config import settings
from acere.instances.paths import get_app_path_handler
from acere.services.scraper import name_processor
from acere.services.scraper.common import ScraperCommon
from acere.services.scraper.models import FoundAceStream
from acere.utils.exception_handling import log_aiohttp_exception
from acere.utils.helpers import slugify
from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from acere.core.config.scraper import ScrapeSiteIPTV, TitleFilter
else:
    ScrapeSiteIPTV = object
    TitleFilter = object

logger = get_logger(__name__)

TVG_LOGO_REGEX = re.compile(r'tvg-logo="([^"]+)"')
TVG_ID_REGEX = re.compile(r'tvg-id="([^"]+)"')
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]+)"')
LAST_FOUND_REGEX = re.compile(r'x-last-found="(\d+)"')

COUNTRY_CODE_REGEX = re.compile(r"\s*\[\w{2}\]\s*$")
COUNTRY_CODE_ALT_REGEX = [
    re.compile(r"\.(\w{2})\s*$"),  # Matches .uk
    re.compile(r"^(\w{2})[ :]"),  # Matches "UK " or "UK: "
]


class IPTVStreamScraper(ScraperCommon):
    """Scraper for IPTV sites to find AceStream streams."""

    async def scrape_iptv_playlists(self, sites: list[ScrapeSiteIPTV]) -> list[FoundAceStream]:
        """Scrape the streams from the configured IPTV sites."""
        found_streams: list[FoundAceStream] = []

        for site in sites:
            streams = await self._scrape_iptv_playlist(site)
            if streams:
                found_streams.extend(streams)

        return found_streams

    async def _scrape_iptv_playlist(self, site: ScrapeSiteIPTV) -> list[FoundAceStream]:
        """Scrape the streams from the configured IPTV sites."""
        content = await self._get_site_content(site)
        logger.trace("Scraping content for IPTV site %s: len=%d", site.name, len(content) if content else 0)
        if not content:
            return []

        found_streams = await self.parse_m3u_content(content, site)

        for stream in found_streams:  # These streams are freshly scraped
            stream.last_scraped_time = datetime.now(tz=UTC)

        logger.debug("Found %d streams on IPTV site %s", len(found_streams), site.name)

        return found_streams

    async def _get_site_content(self, site: ScrapeSiteIPTV) -> str | None:
        """Get site content from cache or by scraping."""
        if self.scraper_cache.is_cache_valid(site.url):
            logger.debug("Loaded IPTV site content from cache for: %s", site.name)
            return self.scraper_cache.load_from_cache(site.url)

        logger.info("Scraping streams from IPTV site: %s", site.name)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(site.url.encoded_string()) as response:
                    response.raise_for_status()
                    content = await response.text(encoding="utf-8")
        except (aiohttp.ClientError, TimeoutError) as e:
            log_aiohttp_exception(logger, site.url, e)
            return None

        logger.debug("Caching IPTV site content for: %s", site.name)
        self.scraper_cache.save_to_cache(site.url, content)

        return content

    # region Line Processing
    async def _found_ace_stream_from_extinf_line(
        self,
        line: str,
        content_id: str,
        infohash: str | None,
        title_filter: TitleFilter,
        site_name: str,
    ) -> FoundAceStream | None:
        """Parse EXTINF line and return title if valid."""
        extinf_parts = 2
        parts = line.split(",", 1)  # Split on first comma only
        if len(parts) != extinf_parts:
            logger.warning("Malformed EXTINF line: %s", line)
            return None

        title = parts[1].strip()

        tvg_id, title = self._extract_tvg_id(line, title)
        override_title = name_processor.get_title_override_from_content_id(content_id or infohash)
        title = override_title or name_processor.cleanup_candidate_title(title)

        tvg_id = name_processor.get_tvg_id_from_title(title)  # Redo since we have our own logic for tvg ids

        if not name_processor.check_title_allowed(title=title, title_filter=title_filter):
            return None

        group_title = self._extract_group_title(line)
        group_title = name_processor.populate_group_title(group_title, title)

        await self._download_tvg_logo(parts[0], title)
        tvg_logo = name_processor.find_tvg_logo_image(title)

        _get_last_found_time_epoch = self._get_last_found_time(line)
        _get_last_found_time = datetime.fromtimestamp(_get_last_found_time_epoch, tz=UTC)

        return FoundAceStream(
            title=title,
            content_id=content_id,
            infohash=infohash,
            tvg_id=tvg_id,
            tvg_logo=tvg_logo,
            group_title=group_title,
            sites_found_on=[site_name],
            last_scraped_time=_get_last_found_time,
        )

    async def parse_m3u_content(self, content: str, site: ScrapeSiteIPTV) -> list[FoundAceStream]:
        """Parse M3U content and extract AceStream entries."""
        found_streams: list[FoundAceStream] = []
        lines = content.splitlines()

        line_one = ""

        for line in lines:
            if line.strip() == "#EXTM3U":
                continue  # First line of a playlist, skip it

            line_normalised = line.replace("#EXTINF:-1,", "#EXTINF:-1").strip()

            # First line of an entry
            if line.startswith("#EXTINF:"):
                line_one = line_normalised
                continue

            # Second line of an entry, creates the ace stream object
            valid_ace_uri = name_processor.check_valid_ace_uri(line_normalised)

            if not line.startswith("#EXTINF:") and valid_ace_uri is not None and line_one:
                content_id = name_processor.extract_content_id_from_url(valid_ace_uri)
                infohash = name_processor.extract_infohash_from_url(valid_ace_uri)

                ace_stream = await self._found_ace_stream_from_extinf_line(
                    line=line_one,
                    content_id=content_id,
                    infohash=infohash,
                    title_filter=site.title_filter,
                    site_name=site.name,
                )
                if ace_stream is not None:
                    found_streams.append(ace_stream)

            line_one = ""

        return found_streams

    def _get_last_found_time(self, line: str) -> int:
        """Extract the last found time from the line."""
        match = LAST_FOUND_REGEX.search(line)
        if match:
            return int(match.group(1))
        return int(datetime.now(tz=UTC).timestamp())  # Could break adhoc?

    def _get_tvg_url(self, line: str) -> HttpUrl | None:
        """Extract the TVG logo URL from the line."""
        match = TVG_LOGO_REGEX.search(line)
        if match:
            return HttpUrl(match.group(1))
        return None

    async def _actually_download_tvg_logo(self, tvg_logo_url: HttpUrl, title: str) -> bytes | None:
        output_logo = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    tvg_logo_url.encoded_string(), timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response.raise_for_status()
                    output_logo = await response.read()
        except (aiohttp.ClientError, TimeoutError) as e:
            error_short = type(e).__name__
            logger.debug("Error downloading TVG logo for %s [%s], %s", title, tvg_logo_url, error_short)

        if "git-lfs" in (output_logo or b"").decode(errors="ignore"):
            logger.warning("TVG logo for %s appears to be a Git LFS placeholder, skipping", title)
            return None

        return output_logo

    async def _download_tvg_logo(self, line: str, title: str) -> None:
        """Download the TVG logo and the URL it got it from."""
        tvg_logos_path = get_app_path_handler().tvg_logos_dir

        title_slug = slugify(title)

        for extension in SUPPORTED_TVG_LOGO_EXTENSIONS:
            logo_path = tvg_logos_path / f"{title_slug}.{extension}"
            if logo_path.is_file():
                return

        # This logic is for if we have imported settings from a github scraper and want to fetch their images.
        if settings.scraper.tvg_logo_external_url is not None:
            for extension in SUPPORTED_TVG_LOGO_EXTENSIONS:
                file_name = f"{title_slug}.{extension}"
                logo = await self._actually_download_tvg_logo(
                    HttpUrl(f"{settings.scraper.tvg_logo_external_url}/{file_name}"),
                    title,
                )
                if logo is not None:
                    logo_path = tvg_logos_path / file_name
                    logo_path.parent.mkdir(parents=True, exist_ok=True)
                    with logo_path.open("wb") as file:
                        file.write(logo)
                    return

        tvg_logo_url = self._get_tvg_url(line)
        if tvg_logo_url is None:
            logger.debug("No TVG logo URL found for %s", title)
            return

        url_file_extension = tvg_logo_url.encoded_string().split(".")[-1]
        url_file_extension = url_file_extension.split("?")[0]
        if url_file_extension.lower() not in SUPPORTED_TVG_LOGO_EXTENSIONS:
            logger.warning(
                "Unsupported TVG logo file extension for %s: %s",
                title,
                url_file_extension,
            )
            return

        logger.info("Downloading TVG logo for %s from m3u8 %s", title, tvg_logo_url)
        content = await self._actually_download_tvg_logo(tvg_logo_url, title)
        if content is None:
            return

        tvg_logo_path = tvg_logos_path / f"{title_slug}.{url_file_extension}"
        tvg_logo_path.parent.mkdir(parents=True, exist_ok=True)
        with tvg_logo_path.open("wb") as file:
            file.write(content)

    def _extract_group_title(self, line: str) -> str:
        """Extract the group title from the line if it exists."""
        match = GROUP_TITLE_REGEX.search(line)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_tvg_id(self, line: str, title: str) -> tuple[str, str]:
        """Extract the TVG ID from the line if it exists, otherwise fallback to name processor.

        Try put the country code in the title if we can.
        """
        original_title = title
        match = TVG_ID_REGEX.search(line)
        if not match:
            logger.debug("No TVG ID found in line, using name processor for title: %s", title)
            return name_processor.get_tvg_id_from_title(title), title
        wip_tvg_id = match.group(1).strip()

        # If we have a country code in the title, we leave it as is
        if COUNTRY_CODE_REGEX.match(title):
            return wip_tvg_id, title

        for regex in COUNTRY_CODE_ALT_REGEX:
            matches = regex.findall(wip_tvg_id)
            if matches:
                country_code = matches[0].upper()
                if not title.endswith(f"[{country_code}]"):
                    title = f"{title} [{country_code}]"
                break

        if original_title != title:
            logger.trace(
                "Extracted TVG ID: %s from line, updated title from: %s to: %s", wip_tvg_id, original_title, title
            )
        else:
            logger.trace("Extracted TVG ID: %s from line for title: %s", wip_tvg_id, title)

        return wip_tvg_id, title
