"""Helper functions for scrapers."""

import re

from .config import TitleFilter
from .logger import get_logger
from .scraper_m3u_name_replacer import M3UNameReplacer
from .scraper_objects import FlatFoundAceStream

logger = get_logger(__name__)

STREAM_TITLE_MAX_LENGTH = 50
ACE_URL_PREFIXES = [
    "acestream://",
    "http://127.0.0.1:6878/ace/getstream?id=",
    "http://127.0.0.1:6878/ace/getstream?content_id=",
    "http://127.0.0.1:6878/ace/manifest.m3u8?id=",
    "http://127.0.0.1:6878/ace/manifest.m3u8?content_id=",  # Side note, this is the good one
]


m3u_replacer = M3UNameReplacer()


def cleanup_candidate_title(title: str) -> str:
    """Cleanup the candidate title."""
    title = title.strip()

    for prefix in ACE_URL_PREFIXES:
        title = title.removeprefix(prefix)

    title = title.split("\n")[0].strip()  # Remove any newlines
    title = re.sub(r"\b[0-9a-fA-F]{40}\b", "", title).strip()  # Remove any ace 40 digit hex ids from the title
    title = m3u_replacer.do_replacements(title)
    return title.strip()


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


def get_streams_as_iptv(streams: list[FlatFoundAceStream], hls_path: str) -> str:
    """Get the found streams as an IPTV M3U8 string."""
    m3u8_content = "#EXTM3U\n"

    for stream in streams:
        logger.debug(stream)
        if stream.quality > 0:
            # Country codes are 2 characters between square brackets, e.g. [US]
            country_code_regex = re.search(r"\[([A-Z]{2})\]", stream.title)
            tvg_id = 'tvg-id=""'

            if country_code_regex and isinstance(country_code_regex.group(1), str):
                country_code = country_code_regex.group(1)
                stream_title_no_cc = stream.title.replace(f"[{country_code}]", "").strip()
                tvg_id = f'tvg-id="{stream_title_no_cc}.{country_code.lower()}"'

            m3u8_content += f"#EXTINF:-1 {tvg_id},{stream.title}\n"
            m3u8_content += f"{hls_path}{stream.ace_id}\n"

    return m3u8_content


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
