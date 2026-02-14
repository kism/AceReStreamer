"""M3U playlist parser for extracting AceStream entries."""

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import HttpUrl

from acere.services.scraper import name_processor
from acere.services.scraper.iptv import tvg_logo
from acere.services.scraper.models import FoundAceStream
from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from acere.core.config.scraper import ScrapeSiteIPTV, TitleFilter
else:
    ScrapeSiteIPTV = object
    TitleFilter = object

logger = get_logger(__name__)

_COUNTRY_CODE_ALT_REGEX: list[re.Pattern] = [
    re.compile(r"\.(\w{2})\s*$"),  # Matches .uk
    re.compile(r"^(\w{2})[ :]"),  # Matches "UK " or "UK: "
]
TVG_LOGO_REGEX = re.compile(r'tvg-logo="([^"]+)"')


class M3UParser:
    """Parser for M3U playlist content to extract AceStream entries.

    This class is stateless and can be reused across multiple parsing operations.
    All parsing logic for M3U8 files is encapsulated here.
    """

    TVG_ID_REGEX = re.compile(r'tvg-id="([^"]+)"')
    GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]+)"')
    LAST_FOUND_REGEX = re.compile(r'x-last-found="(\d+)"')
    COUNTRY_CODE_REGEX = re.compile(r"\s*\[\w{2}\]\s*$")

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

        logo_url = self._extract_logo_url(parts[0])
        await tvg_logo.download_and_save_logo(logo_url, title)
        tvg_logo_path = name_processor.find_tvg_logo_image(title)

        _get_last_found_time_epoch = self._get_last_found_time(line)
        _get_last_found_time = datetime.fromtimestamp(_get_last_found_time_epoch, tz=UTC)

        return FoundAceStream(
            title=title,
            content_id=content_id,
            infohash=infohash,
            tvg_id=tvg_id,
            tvg_logo=tvg_logo_path,
            group_title=group_title,
            sites_found_on=[site_name],
            last_scraped_time=_get_last_found_time,
        )

    def _get_last_found_time(self, line: str) -> int:
        """Extract the last found time from the line."""
        match = self.LAST_FOUND_REGEX.search(line)
        if match:
            return int(match.group(1))
        return int(datetime.now(tz=UTC).timestamp())  # Could break adhoc?

    def _extract_group_title(self, line: str) -> str:
        """Extract the group title from the line if it exists."""
        match = self.GROUP_TITLE_REGEX.search(line)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_logo_url(self, line: str) -> HttpUrl | None:
        """Extract the TVG logo URL from an EXTINF line."""
        match = TVG_LOGO_REGEX.search(line)
        if match:
            return HttpUrl(match.group(1))
        return None

    def _extract_tvg_id(self, line: str, title: str) -> tuple[str, str]:
        """Extract the TVG ID from the line if it exists, otherwise fallback to name processor.

        Try put the country code in the title if we can.
        """
        original_title = title
        match = self.TVG_ID_REGEX.search(line)
        if not match:
            logger.debug("No TVG ID found in line, using name processor for title: %s", title)
            return name_processor.get_tvg_id_from_title(title), title
        wip_tvg_id = match.group(1).strip()

        # If we have a country code in the title, we leave it as is
        if self.COUNTRY_CODE_REGEX.match(title):
            return wip_tvg_id, title

        for regex in _COUNTRY_CODE_ALT_REGEX:
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
