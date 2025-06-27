"""M3U Name Replacer for Ace Streamer Scraper Helper."""

import csv
import re
from pathlib import Path

from acerestreamer.config.models import TitleFilter
from acerestreamer.utils.logger import get_logger

from .models import FlatFoundAceStream

logger = get_logger(__name__)

STREAM_TITLE_MAX_LENGTH = 50
ACE_URL_PREFIXES = [
    "acestream://",
    "http://127.0.0.1:6878/ace/getstream?id=",
    "http://127.0.0.1:6878/ace/getstream?content_id=",
    "http://127.0.0.1:6878/ace/manifest.m3u8?id=",
    "http://127.0.0.1:6878/ace/manifest.m3u8?content_id=",  # Side note, this is the good one
]

# Compiled regex patterns
COUNTRY_CODE_PATTERN = re.compile(r"\[([A-Z]{2})\]")
ACE_ID_PATTERN = re.compile(r"\b[0-9a-fA-F]{40}\b")


class StreamNameProcessor:
    """Cache for M3U text replacements."""

    _CSV_DESIRED_COLUMNS: int = 2

    def __init__(self) -> None:
        """Initialize the cache."""
        self.cache: dict[str, str] = {}
        self.instance_path: Path | None = None

    def load_config(self, instance_path: str | Path) -> None:
        """Initialize the cache."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)

        self.instance_path = instance_path

        # Load the csv
        m3u_path = self.instance_path / "m3u_replacements.csv"
        if not m3u_path.exists():
            m3u_path.touch()
            return

        with m3u_path.open("r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == self._CSV_DESIRED_COLUMNS and not row[0].startswith("#"):
                    self.cache[row[0].strip()] = row[1].strip()

    def do_replacements(self, name: str) -> str:
        """Perform replacements in the M3U content."""
        for key, value in self.cache.items():
            if key in name:
                logger.debug("Replacing '%s' with '%s' in '%s'", key, value, name)
                name = name.replace(key, value)

        return name

    def cleanup_candidate_title(self, title: str) -> str:
        """Cleanup the candidate title."""
        title = title.strip()

        for prefix in ACE_URL_PREFIXES:
            title = title.removeprefix(prefix)

        title = title.split("\n")[0].strip()  # Remove any newlines
        title = ACE_ID_PATTERN.sub("", title).strip()  # Remove any ace 40 digit hex ids from the title
        title = self.do_replacements(title)
        return title.strip()

    def candidates_regex_cleanup(self, candidate_titles: list[str], regex: str) -> list[str]:
        """Cleanup the title using a regex."""
        if regex == "":
            return candidate_titles

        compiled_regex = re.compile(regex)
        new_candidate_titles = []

        for title in candidate_titles:
            title_new = compiled_regex.sub("", title).strip()
            if title_new != "":
                new_candidate_titles.append(title_new)

        return new_candidate_titles

    def get_streams_as_iptv(self, streams: list[FlatFoundAceStream], hls_path: str) -> str:
        """Get the found streams as an IPTV M3U8 string."""
        m3u8_content = "#EXTM3U\n"

        for stream in streams:
            logger.debug(stream)
            if stream.has_ever_worked:
                # Country codes are 2 characters between square brackets, e.g. [US]
                tvg_id = f'tvg-id="{stream.tvg_id}"'

                m3u8_content += f"#EXTINF:-1 {tvg_id},{stream.title}\n"
                m3u8_content += f"{hls_path}{stream.ace_id}\n"

        return m3u8_content

    def get_tvg_id_from_title(self, title: str) -> str:
        """Extract the TVG ID from the title."""
        country_code_regex = COUNTRY_CODE_PATTERN.search(title)
        if country_code_regex and isinstance(country_code_regex.group(1), str):
            country_code = country_code_regex.group(1)
            title_no_cc = title.replace(f"[{country_code}]", "").strip()
            return f"{title_no_cc}.{country_code.lower()}"
        return ""

    def extract_ace_id_from_url(self, url: str) -> str:
        """Extract the AceStream ID from a URL."""
        url = url.strip()
        for prefix in ACE_URL_PREFIXES:
            url = url.replace(prefix, "")

        if "&" in url:
            url = url.split("&")[0]

        return url

    def check_valid_ace_url(self, url: str) -> bool:
        """Check if the AceStream URL is valid."""
        return any(url.startswith(prefix) for prefix in ACE_URL_PREFIXES)

    def check_title_allowed(self, title: str, title_filter: TitleFilter) -> bool:
        """Check if the title contains any disallowed words."""
        if not title:
            return False

        title = title.lower()

        if any(word.lower() in title for word in title_filter.always_exclude_words):
            logger.trace("Title '%s' is not allowed, skipping", title)
            return False

        if any(word.lower() in title for word in title_filter.always_include_words):
            return True

        if any(word.lower() in title for word in title_filter.exclude_words):
            logger.trace("Title '%s' is not allowed, skipping", title)
            return False

        if title_filter.include_words:
            return any(word.lower() in title for word in title_filter.include_words)

        return True

    def trim_title(self, title: str) -> str:
        """Trim the title to a maximum length, only really needs to be used for HTML titles."""
        if len(title) > STREAM_TITLE_MAX_LENGTH:
            return title[:STREAM_TITLE_MAX_LENGTH].strip()
        return title.strip()
