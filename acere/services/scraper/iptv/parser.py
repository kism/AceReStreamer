"""M3U playlist parser for extracting AceStream entries."""

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import HttpUrl, ValidationError

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

_COUNTRY_CODE_ALT_REGEX: list[re.Pattern[str]] = [
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

        # Split into sections - each section starts with #EXTINF
        sections = self._split_into_sections(lines)

        for section in sections:
            if not section:
                continue

            # First line is always #EXTINF
            extinf_line = section[0].strip()

            # Collect metadata and find acestream URL
            metadata: dict[str, str] = {}
            acestream_url = None

            for line in section[1:]:
                line_stripped = line.strip()

                # Collect metadata lines
                if line_stripped.startswith("#EXTTV:"):
                    metadata["exttv"] = line_stripped[7:].strip()
                elif line_stripped.startswith("#EXTLOGO:"):
                    metadata["extlogo"] = line_stripped[9:].strip()
                else:
                    # Check if this is the acestream URL
                    valid_ace_uri = name_processor.check_valid_ace_uri(line_stripped)
                    if valid_ace_uri is not None:
                        acestream_url = valid_ace_uri
                        break  # URL is the last meaningful line

            # Process the entry if we found an acestream URL
            if acestream_url:
                content_id = name_processor.extract_content_id_from_url(acestream_url)
                infohash = name_processor.extract_infohash_from_url(acestream_url)

                ace_stream = await self._found_ace_stream_from_extinf_line(
                    line=extinf_line,
                    content_id=content_id,
                    infohash=infohash,
                    site=site,
                    metadata=metadata or None,
                )
                if ace_stream is not None:
                    found_streams.append(ace_stream)

        return found_streams

    def _split_into_sections(self, lines: list[str]) -> list[list[str]]:
        """Split lines into sections, each starting with #EXTINF."""
        sections: list[list[str]] = []
        current_section: list[str] = []

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines and #EXTM3U header
            if not line_stripped or line_stripped == "#EXTM3U":
                continue

            # Start new section when we see #EXTINF
            if line_stripped.startswith("#EXTINF:"):
                if current_section:
                    sections.append(current_section)
                current_section = [line_stripped]
            elif current_section:
                # Add line to current section
                current_section.append(line_stripped)

        # Don't forget the last section
        if current_section:
            sections.append(current_section)

        return sections

    async def _found_ace_stream_from_extinf_line(
        self,
        line: str,
        content_id: str,
        infohash: str | None,
        site: ScrapeSiteIPTV,
        metadata: dict[str, str] | None = None,
    ) -> FoundAceStream | None:
        """Parse EXTINF line and return title if valid."""
        extinf_parts = 2
        parts = line.split(",", 1)  # Split on first comma only
        if len(parts) != extinf_parts:
            logger.warning("Malformed EXTINF line: %s", line)
            return None

        title = parts[1].strip()

        tvg_id, title = self._extract_tvg_id(line, title, metadata)
        override_title = name_processor.get_title_override_from_content_id(content_id or infohash)
        title = override_title or name_processor.cleanup_candidate_title(title)

        tvg_id = name_processor.get_tvg_id_from_title(title)  # Redo since we have our own logic for tvg ids

        if not name_processor.check_title_allowed(title=title, title_filter=site.title_filter):
            return None

        group_title = self._extract_group_title(line)
        group_title = name_processor.populate_group_title(group_title, title)

        logo_url = self._extract_logo_url(parts[0], metadata)
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
            sites_found_on=[site.name],
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

    def _extract_logo_url(self, line: str, metadata: dict[str, str] | None = None) -> HttpUrl | None:
        """Extract the TVG logo URL from an EXTINF line or metadata."""
        # Check if we have EXTLOGO metadata first
        if metadata and "extlogo" in metadata:
            try:
                return HttpUrl(metadata["extlogo"])
            except ValidationError as e:
                logger.debug("Failed to parse EXTLOGO URL: %s", e)

        # Fall back to tvg-logo attribute
        match = TVG_LOGO_REGEX.search(line)
        if match:
            try:
                return HttpUrl(match.group(1))
            except ValidationError as e:
                logger.debug("Failed to parse TVG logo URL: %s", e)
        return None

    def _extract_tvg_id(  # noqa: C901 Don't care since I put the functions in the function
        self,
        line: str,
        title: str,
        metadata: dict[str, str] | None = None,
    ) -> tuple[str, str]:
        """Extract the TVG ID from the line or metadata.

        Try put the country code in the title if we can.
        """

        def _extract_tvg_id_from_exttv(exttv_line: str) -> str | None:
            """Extract TVG ID from EXTTV line."""
            parts = exttv_line.split(";")
            if len(parts) >= 3:  # noqa: PLR2004 #EXTTV has three parts, the third part is the TVG ID
                tvg_id = parts[2].strip()
                return tvg_id or None
            return None

        def _extract_country_from_exttv(exttv_line: str) -> str | None:
            """Extract country code from EXTTV line."""
            parts = exttv_line.split(";")
            if len(parts) >= 2:  # noqa: PLR2004 #EXTTV has three parts, the second part is the country code
                country = parts[1].strip()
                if country:
                    return country.upper()
            return None

        original_title = title

        # Check if we have EXTTV metadata first
        if metadata and "exttv" in metadata:
            tvg_id = _extract_tvg_id_from_exttv(metadata["exttv"])
            country = _extract_country_from_exttv(metadata["exttv"])

            if tvg_id:
                # Add country code to title if present
                if country and not title.endswith(f"[{country}]"):
                    title = f"{title} [{country}]"
                    logger.trace("Added country code from EXTTV to title: %s", title)
                return tvg_id, title

        # Fall back to existing logic for EXTINF attributes
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
