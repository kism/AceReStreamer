"""Generic M3U playlist parser shared between Ace and IPTV scrapers."""

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from acere.utils.logger import get_logger

logger = get_logger(__name__)

TVG_ID_REGEX = re.compile(r'tvg-id="([^"]+)"')
TVG_LOGO_REGEX = re.compile(r'tvg-logo="([^"]+)"')
GROUP_TITLE_REGEX = re.compile(r'group-title="([^"]+)"')
LAST_FOUND_REGEX = re.compile(r'x-last-found="(\d+)"')


@dataclass
class M3UEntry:
    """A single entry parsed from an M3U playlist."""

    title: str
    url: str
    tvg_id: str = ""
    tvg_logo_url: str = ""
    group_title: str = ""
    last_found: int = 0
    metadata: dict[str, str] = field(default_factory=dict)


class GenericM3UParser:
    """Stateless parser that extracts M3UEntry objects from M3U content.

    This parser is scheme-agnostic: it captures the URL line as a raw string
    without validating whether it is an acestream://, http://, or any other scheme.
    Consumers are responsible for filtering entries by URL type.
    """

    def parse(self, content: str) -> list[M3UEntry]:
        """Parse M3U content into a list of M3UEntry objects."""
        entries: list[M3UEntry] = []
        sections = self._split_into_sections(content.splitlines())

        for section in sections:
            if not section:
                continue
            entry = self._parse_section(section)
            if entry is not None:
                entries.append(entry)

        return entries

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
                current_section.append(line_stripped)

        if current_section:
            sections.append(current_section)

        return sections

    def _parse_section(self, section: list[str]) -> M3UEntry | None:
        """Parse a section into an M3UEntry."""
        extinf_line = section[0]

        # Parse title from EXTINF line
        extinf_parts = 2
        parts = extinf_line.split(",", 1)
        if len(parts) != extinf_parts:
            logger.warning("Malformed EXTINF line: %s", extinf_line)
            return None

        title = parts[1].strip()
        attrs = parts[0]

        # Extract attributes from EXTINF line
        tvg_id = self._extract_regex(TVG_ID_REGEX, attrs)
        tvg_logo_url = self._extract_regex(TVG_LOGO_REGEX, attrs)
        group_title = self._extract_regex(GROUP_TITLE_REGEX, attrs)
        last_found = self._extract_last_found(attrs)

        # Collect metadata and find the URL line
        metadata: dict[str, str] = {}
        url = ""

        for line in section[1:]:
            if line.startswith("#EXTTV:"):
                metadata["exttv"] = line[7:].strip()
            elif line.startswith("#EXTLOGO:"):
                metadata["extlogo"] = line[9:].strip()
            elif not line.startswith("#"):
                url = line
                break

        if not url:
            return None

        return M3UEntry(
            title=title,
            url=url,
            tvg_id=tvg_id,
            tvg_logo_url=tvg_logo_url,
            group_title=group_title,
            last_found=last_found,
            metadata=metadata,
        )

    def _extract_regex(self, pattern: re.Pattern[str], text: str) -> str:
        """Extract a value using a regex pattern, return empty string if not found."""
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_last_found(self, text: str) -> int:
        """Extract the x-last-found epoch timestamp."""
        match = LAST_FOUND_REGEX.search(text)
        if match:
            return int(match.group(1))
        return int(datetime.now(tz=UTC).timestamp())
