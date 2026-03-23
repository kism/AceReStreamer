"""Ace-specific name processing functions for AceStream scraper."""

import re

from pydantic import AnyUrl, ValidationError

from acere.instances.config import settings
from acere.utils.helpers import check_valid_content_id_or_infohash
from acere.utils.logger import get_logger

logger = get_logger(__name__)

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
    "http://acestream:6878/ace/getstream?infohash=",
    "http://127.0.0.1:6878/ace/manifest.m3u8?infohash=",
    "http://acestream:6878/ace/manifest.m3u8?infohash=",
]

# Compiled regex patterns
ACE_ID_PATTERN = re.compile(r"\b[0-9a-fA-F]{40}\b")


def cleanup_ace_candidate_title(title: str) -> str:
    """Cleanup the candidate title."""
    title = title.strip()

    for prefix in ACE_URL_PREFIXES_CONTENT_ID:
        title = title.removeprefix(prefix)

    title = title.split("\n")[0]  # Remove any newlines
    title = ACE_ID_PATTERN.sub("", title)  # Remove any ace 40 digit hex ids from the title
    return title.strip()


def _extract_from_url(url: AnyUrl, prefix_list: list[str]) -> str:
    """Extract a part of the URL based on the provided prefixes."""
    result = url.encoded_string()

    for prefix in prefix_list:
        if result.startswith(prefix):
            result = result.removeprefix(prefix)
            if check_valid_content_id_or_infohash(result):
                return result

    return ""


def extract_content_id_from_url(url: AnyUrl) -> str:
    """Extract the AceStream ID from a URI."""
    return _extract_from_url(url, ACE_URL_PREFIXES_CONTENT_ID)


def extract_infohash_from_url(url: AnyUrl) -> str | None:
    """Extract the AceStream infohash from a URL."""
    return _extract_from_url(url, ACE_URL_PREFIXES_INFOHASH) or None  # Infohash shouldn't be ""


def check_valid_ace_uri(url: AnyUrl | str) -> AnyUrl | None:
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


def get_title_override_from_content_id(content_id: str | None) -> str | None:
    """Get a title override from the content ID if it exists."""
    if content_id is None:
        return None
    return settings.ace.scraper.content_id_infohash_name_overrides.get(content_id)
