"""M3U Name Replacer for Ace Streamer Scraper Helper."""

import re
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import AnyUrl, ValidationError

from acere.utils.constants import SUPPORTED_TVG_LOGO_EXTENSIONS
from acere.utils.helpers import check_valid_content_id_or_infohash, slugify
from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from acere.core.config import TitleFilter

    from .models import FoundAceStreamAPI
else:
    FoundAceStreamAPI = object
    TitleFilter = object

logger = get_logger(__name__)

STREAM_TITLE_MAX_LENGTH = 50
ACE_URL_PREFIXES_CONTENT_ID = [
    "acestream://",
    "http://127.0.0.1:6878/ace/getstream?id=",
    "http://127.0.0.1:6878/ace/getstream?content_id=",
    "http://127.0.0.1:6878/ace/manifest.m3u8?id=",
    "http://127.0.0.1:6878/ace/manifest.m3u8?content_id=",  # Side note, this is the good one when using ace
    "plugin://script.module.horus?action=play&id=",  # Horus Kodi plugin
]
ACE_URL_PREFIXES_INFOHASH = [
    "http://127.0.0.1:6878/ace/getstream?infohash=",
    "http://127.0.0.1:6878/ace/manifest.m3u8?infohash=",
]

# Compiled regex patterns
COUNTRY_CODE_PATTERN = re.compile(r"\[([A-Z]{2})\]")
ACE_ID_PATTERN = re.compile(r"\b[0-9a-fA-F]{40}\b")

COMPILED_REGEX_CACHE: dict[str, re.Pattern[str]] = {}


class StreamNameProcessor:
    """Cache for M3U text replacements."""

    _CSV_DESIRED_COLUMNS: int = 2

    def __init__(self) -> None:
        """Initialize the cache."""
        self._name_replacements: dict[str, str] = {}
        self._instance_path: Path | None = None

    def load_config(
        self,
        instance_path: str | Path,
        name_replacements: dict[str, str],
        category_mapping: dict[str, list[str]],
    ) -> None:
        """Initialize the cache."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)

        self._instance_path = instance_path
        self._name_replacements = name_replacements
        self._category_mapping = category_mapping

    def _do_replacements(self, name: str) -> str:
        """Perform replacements in the M3U content."""
        for key, value in self._name_replacements.items():
            if key in name:
                logger.trace("Replacing '%s' with '%s' in '%s'", key, value, name)
                name = name.replace(key, value)

        return name

    def cleanup_candidate_title(self, title: str) -> str:
        """Cleanup the candidate title."""
        title = title.strip()

        for prefix in ACE_URL_PREFIXES_CONTENT_ID:
            title = title.removeprefix(prefix)

        title = title.split("\n")[0].strip()  # Remove any newlines
        title = ACE_ID_PATTERN.sub("", title).strip()  # Remove any ace 40 digit hex ids from the title
        title = self._do_replacements(title)
        return title.strip()

    def candidates_regex_cleanup(self, candidate_titles: list[str], regex_list: list[str]) -> list[str]:
        """Cleanup the title using a regex."""
        if not regex_list:
            return candidate_titles

        new_candidate_titles = []

        # For each candidate title
        for title in candidate_titles:
            wip_title = title
            for regex_str in regex_list:
                compiled_regex = COMPILED_REGEX_CACHE.get(regex_str)
                if compiled_regex is None:
                    compiled_regex = re.compile(regex_str)
                    COMPILED_REGEX_CACHE[regex_str] = compiled_regex

                wip_title = compiled_regex.sub("", wip_title).strip()

            wip_title = wip_title.strip()

            # If name is not empty or only non-alphanumeric characters, add it
            if wip_title != "" and not all(not c.isalnum() for c in wip_title):
                new_candidate_titles.append(wip_title)

        return new_candidate_titles

    def get_tvg_id_from_title(self, title: str) -> str:
        """Extract the TVG ID from the title."""
        country_code_regex = COUNTRY_CODE_PATTERN.search(title)
        if country_code_regex and isinstance(country_code_regex.group(1), str):
            country_code = country_code_regex.group(1)
            title_no_cc = title.replace(f"[{country_code}]", "").strip()
            return f"{title_no_cc}.{country_code.lower()}"
        return ""

    def _extract_from_url(self, url: AnyUrl, prefix_list: list[str]) -> str:
        """Extract a part of the URL based on the provided prefixes."""
        result = url.encoded_string()

        for prefix in prefix_list:
            if result.startswith(prefix):
                result = result.removeprefix(prefix)
                if check_valid_content_id_or_infohash(result):
                    return result

        return ""

    def extract_content_id_from_url(self, url: AnyUrl) -> str:
        """Extract the AceStream ID from a URI."""
        return self._extract_from_url(url, ACE_URL_PREFIXES_CONTENT_ID)

    def extract_infohash_from_url(self, url: AnyUrl) -> str:
        """Extract the AceStream infohash from a URL."""
        return self._extract_from_url(url, ACE_URL_PREFIXES_INFOHASH)

    def check_valid_ace_uri(self, url: AnyUrl | str) -> AnyUrl | None:
        """Check if the AceStream URL is valid."""
        # Validate the URL format
        if isinstance(url, str):
            try:
                url = AnyUrl(url)
            except ValidationError:
                return None

        # Back to a string to check the prefixes
        url_str = url.encoded_string()

        valid = any(url_str.startswith(prefix) for prefix in ACE_URL_PREFIXES_CONTENT_ID) or any(
            url_str.startswith(prefix) for prefix in ACE_URL_PREFIXES_INFOHASH
        )

        if not valid:
            return None

        return url

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
            allowed = any(word.lower() in title for word in title_filter.include_words)
            if not allowed:
                pass
            else:
                logger.trace("Title '%s' is allowed due to include_words", title)

            return allowed

        logger.trace("Title '%s' is default allowed", title)
        return True

    def trim_title(self, title: str) -> str:
        """Trim the title to a maximum length, only really needs to be used for HTML titles."""
        if len(title) > STREAM_TITLE_MAX_LENGTH:
            return title[:STREAM_TITLE_MAX_LENGTH].strip()
        return title.strip()

    def find_tvg_logo_image(self, title: str) -> str:
        """Find the TVG logo image for a given title."""
        if self._instance_path is None:
            return ""

        title_slug = slugify(title)

        for extension in SUPPORTED_TVG_LOGO_EXTENSIONS:
            logo_path = self._instance_path / "tvg_logos" / f"{title_slug}.{extension}"
            if logo_path.is_file():
                return f"{title_slug}.{extension}"

        logger.warning("TVG logo not found, download manually and name it: %s.png", title_slug)

        return ""

    def populate_group_title(self, group_title: str, title: str) -> str:
        """Cleanup the group title."""
        # Put into sentence case
        for category, keywords in self._category_mapping.items():
            # For example, if the catetory is Sports but the group title is sport
            if any(keyword in group_title.lower() for keyword in keywords):
                group_title = category
                break

            # For example, if no group title, but the title contains football etc
            if any(keyword in title.lower() for keyword in keywords):
                group_title = category
                break

        group_title = group_title.strip().capitalize()

        return group_title if group_title else "General"
