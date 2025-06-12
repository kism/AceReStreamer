"""Helper functions for scrapers."""

import re

from .config import TitleFilter
from .logger import get_logger
from .scraper_objects import FlatFoundAceStream

logger = get_logger(__name__)

STREAM_TITLE_MAX_LENGTH = 50
ACE_ID_LENGTH = 40
ACE_URL_PREFIXES = ["http://127.0.0.1:6878/ace/getstream?id=", "acestream://"]


def cleanup_candidate_title(title: str) -> str:
    """Cleanup the candidate title."""
    title = title.strip()

    for prefix in ACE_URL_PREFIXES:
        title = title.removeprefix(prefix)

    title = title.split("\n")[0].strip()  # Remove any newlines
    # Remove any ace 40 digit hex ids from the title
    return re.sub(r"\b[0-9a-fA-F]{40}\b", "", title).strip()


def candidates_regex_cleanup(candidate_titles: list[str], regex: str) -> list[str]:
    """Cleanup the title using a regex."""
    if regex == "":
        return candidate_titles

    new_candidate_titles = []

    for title in candidate_titles:
        title_new = re.sub(regex, "", title).strip()
        if title_new != "":
            new_candidate_titles.append(title_new)

    return new_candidate_titles


def get_streams_as_iptv(streams: list[FlatFoundAceStream], base_url_hls: str) -> str:
    """Get the found streams as an IPTV M3U8 string."""
    m3u8_content = "#EXTM3U\n"

    for stream in streams:
        logger.debug(stream)
        if stream.quality > 0:
            m3u8_content += f"#EXTINF:-1 ,{stream.title}\n"
            m3u8_content += f"{base_url_hls}{stream.ace_id}\n"

    return m3u8_content


def check_valid_ace_id(ace_id: str) -> bool:
    """Check if the AceStream ID is valid."""
    if len(ace_id) != ACE_ID_LENGTH:
        logger.warning("AceStream ID is not the expected length (%d), skipping: %s", ACE_ID_LENGTH, ace_id)
        return False

    if not re.match(r"^[0-9a-fA-F]+$", ace_id):
        logger.warning("AceStream ID contains invalid characters: %s", ace_id)
        return False

    return True


def extract_ace_id_from_url(url: str) -> str:
    """Extract the AceStream ID from a URL."""
    url = url.strip()
    for prefix in ACE_URL_PREFIXES:
        url = url.replace(prefix, "")

    if "&" in url:
        url = url.split("&")[0]

    return url


def check_valid_ace_url(url: str) -> bool:
    """Check if the AceStream URL is valid."""
    return any(url.startswith(prefix) for prefix in ACE_URL_PREFIXES)


def check_title_allowed(title: str, title_filter: TitleFilter) -> bool:
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
