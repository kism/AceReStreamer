"""M3U playlist parser for extracting AceStream entries."""

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import HttpUrl, ValidationError

from acere.services.scraper import name_processor, tvg_logo
from acere.services.scraper.ace import name_processor as ace_name_processor
from acere.services.scraper.ace.models import FoundAceStream
from acere.services.scraper.m3u_common import GenericM3UParser, M3UEntry
from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from acere.config.ace.scraper import ScrapeSiteIPTV, TitleFilter
else:
    ScrapeSiteIPTV = object
    TitleFilter = object

logger = get_logger(__name__)

_COUNTRY_CODE_ALT_REGEX: list[re.Pattern[str]] = [
    re.compile(r"\.(\w{2})\s*$"),  # Matches .uk
    re.compile(r"^(\w{2})[ :]"),  # Matches "UK " or "UK: "
]


class AceM3UParser:
    """Parser for M3U playlist content to extract AceStream entries.

    Uses GenericM3UParser for raw M3U parsing, then applies AceStream-specific
    filtering and processing.
    """

    COUNTRY_CODE_REGEX = re.compile(r"\s*\[\w{2}\]\s*$")

    def __init__(self) -> None:
        """Initialize with a generic M3U parser."""
        self._generic_parser = GenericM3UParser()

    async def parse_m3u_content(self, content: str, site: ScrapeSiteIPTV) -> list[FoundAceStream]:
        """Parse M3U content and extract AceStream entries."""
        entries = self._generic_parser.parse(content)
        found_streams: list[FoundAceStream] = []

        for entry in entries:
            # Check if the URL is a valid ace URI
            valid_ace_uri = ace_name_processor.check_valid_ace_uri(entry.url)
            if valid_ace_uri is None:
                continue

            content_id = ace_name_processor.extract_content_id_from_url(valid_ace_uri)
            infohash = ace_name_processor.extract_infohash_from_url(valid_ace_uri)

            ace_stream = await self._build_found_ace_stream(
                entry=entry,
                content_id=content_id,
                infohash=infohash,
                site=site,
            )
            if ace_stream is not None:
                found_streams.append(ace_stream)

        return found_streams

    async def _build_found_ace_stream(
        self,
        entry: M3UEntry,
        content_id: str,
        infohash: str | None,
        site: ScrapeSiteIPTV,
    ) -> FoundAceStream | None:
        """Build a FoundAceStream from a generic M3UEntry."""
        title = entry.title

        tvg_id, title = self._extract_tvg_id(entry, title)
        override_title = ace_name_processor.get_title_override_from_content_id(content_id or infohash)
        title = override_title or ace_name_processor.cleanup_ace_candidate_title(title)

        tvg_id = name_processor.get_tvg_id_from_title(title)  # Redo since we have our own logic for tvg ids

        if not site.title_filter.check_allowed(title):
            return None

        group_title = entry.group_title
        group_title = name_processor.populate_group_title(group_title, title)

        logo_url = self._extract_logo_url(entry)
        await tvg_logo.download_and_save_logo(logo_url, title)
        tvg_logo_path = name_processor.find_tvg_logo_image(title)

        last_found_time = datetime.fromtimestamp(entry.last_found, tz=UTC)

        return FoundAceStream(
            title=title,
            content_id=content_id,
            infohash=infohash,
            tvg_id=tvg_id,
            tvg_logo=tvg_logo_path,
            group_title=group_title,
            sites_found_on=[site.name],
            last_scraped_time=last_found_time,
        )

    def _extract_logo_url(self, entry: M3UEntry) -> HttpUrl | None:
        """Extract the TVG logo URL from an M3UEntry."""
        # Check EXTLOGO metadata first
        if "extlogo" in entry.metadata:
            try:
                return HttpUrl(entry.metadata["extlogo"])
            except ValidationError as e:
                logger.debug("Failed to parse EXTLOGO URL: %s", e)

        # Fall back to tvg-logo from EXTINF attributes
        if entry.tvg_logo_url:
            try:
                return HttpUrl(entry.tvg_logo_url)
            except ValidationError as e:
                logger.debug("Failed to parse TVG logo URL: %s", e)
        return None

    def _extract_tvg_id(  # noqa: C901 Don't care since I put the functions in the function
        self,
        entry: M3UEntry,
        title: str,
    ) -> tuple[str, str]:
        """Extract the TVG ID from the entry or metadata.

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
        if "exttv" in entry.metadata:
            tvg_id = _extract_tvg_id_from_exttv(entry.metadata["exttv"])
            country = _extract_country_from_exttv(entry.metadata["exttv"])

            if tvg_id:
                # Add country code to title if present
                if country and not title.endswith(f"[{country}]"):
                    title = f"{title} [{country}]"
                    logger.trace("Added country code from EXTTV to title: %s", title)
                return tvg_id, title

        # Fall back to tvg-id from EXTINF attributes
        if not entry.tvg_id:
            logger.debug("No TVG ID found, using name processor for title: %s", title)
            return name_processor.get_tvg_id_from_title(title), title

        wip_tvg_id = entry.tvg_id

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
            logger.trace("Extracted TVG ID: %s, updated title from: %s to: %s", wip_tvg_id, original_title, title)
        else:
            logger.trace("Extracted TVG ID: %s for title: %s", wip_tvg_id, title)

        return wip_tvg_id, title
