"""Scraper for IPTV sites to find AceStream streams."""

import re
from typing import TYPE_CHECKING

import requests
from pydantic import ValidationError

from acerestreamer.utils import slugify
from acerestreamer.utils.constants import SUPPORTED_TVG_LOGO_EXTENSIONS
from acerestreamer.utils.logger import get_logger

from .common import ScraperCommon
from .models import FoundAceStream

if TYPE_CHECKING:
    from acerestreamer.config import ScrapeSiteIPTV, TitleFilter
else:
    ScrapeSiteIPTV = object
    TitleFilter = object

logger = get_logger(__name__)

TVG_LOGO_REGEX = re.compile(r'tvg-logo="([^"]+)"')
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]+)"')


class IPTVStreamScraper(ScraperCommon):
    """Scraper for IPTV sites to find AceStream streams."""

    def scrape_iptv_playlists(self, sites: list[ScrapeSiteIPTV]) -> list[FoundAceStream]:
        """Scrape the streams from the configured IPTV sites."""
        found_streams: list[FoundAceStream] = []

        for site in sites:
            streams = self._scrape_iptv_playlist(site)
            if streams:
                found_streams.extend(streams)

        return found_streams

    def _scrape_iptv_playlist(self, site: ScrapeSiteIPTV) -> list[FoundAceStream]:
        """Scrape the streams from the configured IPTV sites."""
        content = self._get_site_content(site)
        if not content:
            return []

        found_streams = self._parse_m3u_content(content, site)

        logger.debug("Found %d streams on IPTV site %s", len(found_streams), site.name)

        return found_streams

    def _get_site_content(self, site: ScrapeSiteIPTV) -> str | None:
        """Get site content from cache or by scraping."""
        cached_content = self.scraper_cache.load_from_cache(site.url)

        if self.scraper_cache.is_cache_valid(site.url):
            return cached_content

        logger.debug("Scraping streams from IPTV site: %s", site)
        try:
            response = requests.get(site.url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            error_short = type(e).__name__
            logger.error("Error scraping IPTV site %s, %s", site.url, error_short)  # noqa: TRY400 Short error for requests
            return None

        response.encoding = "utf-8"
        content = response.text
        self.scraper_cache.save_to_cache(site.url, content)

        return content

    # region Line Processing
    def _found_ace_stream_from_extinf_line(
        self,
        line: str,
        content_id: str,
        infohash: str,
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

        if not self.name_processor.check_title_allowed(title=title, title_filter=title_filter):
            return None

        title = self.name_processor.cleanup_candidate_title(title)
        tvg_id = self.name_processor.get_tvg_id_from_title(title)

        group_title = self._extract_group_title(line)
        group_title = self.name_processor.populate_group_title(group_title, title)

        self._download_tvg_logo(parts[0], title)
        tvg_logo = self.name_processor.find_tvg_logo_image(title)

        try:
            found_ace_stream = FoundAceStream(
                title=title,
                content_id=content_id,
                infohash=infohash,
                tvg_id=tvg_id,
                tvg_logo=tvg_logo,
                group_title=group_title,
                site_names=[site_name],
            )
        except ValidationError:
            msg = "Validation error creating FoundAceStream object:\n"
            msg += f"Tried title: {title}, content_id: {content_id}, tvg_id: {tvg_id}, tvg_logo: {tvg_logo}"
            msg += f" for line: \n{line}"
            logger.error(msg)  # noqa: TRY400
            return None
        return found_ace_stream

    def _parse_m3u_content(self, content: str, site: ScrapeSiteIPTV) -> list[FoundAceStream]:
        """Parse M3U content and extract AceStream entries."""
        found_streams: list[FoundAceStream] = []
        lines = content.splitlines()

        line_one = ""

        for line in lines:
            line_normalised = line.replace("#EXTINF:-1,", "#EXTINF:-1").strip()

            # First line of an entry
            if line.startswith("#EXTINF:"):
                line_one = line_normalised
                continue

            # Second line of an entry, creates the ace stream object
            if (
                not line.startswith("#EXTINF:")
                and self.name_processor.check_valid_ace_url(line_normalised)
                and line_one
            ):
                content_id = self.name_processor.extract_content_id_from_url(line_normalised)
                infohash = self.name_processor.extract_infohash_from_url(line_normalised)

                ace_stream = self._found_ace_stream_from_extinf_line(
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

    def _download_tvg_logo(self, tvg_logo_url: str, title: str) -> None:
        """Download the TVG logo and return the local path."""
        if self.instance_path is None:
            return

        title_slug = slugify(title)

        for extension in SUPPORTED_TVG_LOGO_EXTENSIONS:
            logo_path = self.instance_path / "tvg_logos" / f"{title_slug}.{extension}"
            if logo_path.is_file():
                return

        regex_result = TVG_LOGO_REGEX.search(tvg_logo_url)

        if not regex_result:
            return

        tvg_logo_url = regex_result.group(1)

        url_file_extension = tvg_logo_url.split(".")[-1]
        url_file_extension = url_file_extension.split("?")[0]
        if url_file_extension.lower() not in SUPPORTED_TVG_LOGO_EXTENSIONS:
            logger.warning("Unsupported TVG logo file extension for %s: %s", title, url_file_extension)
            return

        logger.trace("Downloading TVG logo for %s from %s", title, tvg_logo_url)
        try:
            response = requests.get(tvg_logo_url, timeout=1)
            response.raise_for_status()
        except requests.RequestException as e:
            error_short = type(e).__name__
            logger.error("Error downloading TVG logo for %s, %s", title, error_short)  # noqa: TRY400 Short error for requests
            return

        tvg_logo_path = self.instance_path / "tvg_logos" / f"{title_slug}.{url_file_extension}"
        tvg_logo_path.parent.mkdir(parents=True, exist_ok=True)
        with tvg_logo_path.open("wb") as file:
            file.write(response.content)

    def _extract_group_title(self, line: str) -> str:
        """Extract the group title from the line if it exists."""
        match = GROUP_TITLE_REGEX.search(line)
        if match:
            return match.group(1).strip()
        return ""
