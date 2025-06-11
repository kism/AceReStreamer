"""Helper functions for scrapers."""

import re

from .logger import get_logger
from .scraper_objects import FlatFoundAceStream

logger = get_logger(__name__)

STREAM_TITLE_MAX_LENGTH = 50


def cleanup_candidate_title(title: str) -> str:
    """Cleanup the candidate title."""
    title = title.strip()
    title = title.split("acestream://")[-1].strip()
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
