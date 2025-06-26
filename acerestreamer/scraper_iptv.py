"""Scraper for IPTV sites to find AceStream streams."""

import requests

from .config import ScrapeSiteIPTV, TitleFilter
from .helpers import check_valid_ace_id
from .logger import get_logger
from .scraper_cache import scraper_cache
from .scraper_helpers import (
    check_title_allowed,
    check_valid_ace_url,
    cleanup_candidate_title,
    extract_ace_id_from_url,
    get_tvg_id_from_title,
)
from .scraper_objects import FoundAceStream, FoundAceStreams

logger = get_logger(__name__)


def scrape_streams_iptv_sites(sites: list[ScrapeSiteIPTV]) -> list[FoundAceStreams]:
    """Scrape the streams from the configured IPTV sites."""
    found_streams: list[FoundAceStreams] = []

    for site in sites:
        streams = scrape_streams_iptv_site(site)
        if streams:
            found_streams.append(streams)

    return found_streams


def _parse_extinf_line(line: str, title_filter: TitleFilter) -> str:
    """Parse EXTINF line and return title if valid."""
    extinf_parts = 2
    parts = line.split(",", 1)  # Split on first comma only
    if len(parts) != extinf_parts:
        logger.warning("Malformed EXTINF line: %s", line)
        return ""

    title = parts[1].strip()

    if not check_title_allowed(title=title, title_filter=title_filter):
        return ""

    return cleanup_candidate_title(title)


def _create_ace_stream_from_url(url: str, title: str) -> FoundAceStream | None:
    """Create FoundAceStream from URL and title if valid."""
    ace_id = extract_ace_id_from_url(url)
    tvg_id = get_tvg_id_from_title(title)

    if not check_valid_ace_id(ace_id):
        logger.warning("Invalid Ace ID found in candidate: %s, skipping", ace_id)
        return None

    return FoundAceStream(title=title, ace_id=ace_id, tvg_id=tvg_id)


def _parse_m3u_content(content: str, site: ScrapeSiteIPTV) -> list[FoundAceStream]:
    """Parse M3U content and extract AceStream entries."""
    found_streams: list[FoundAceStream] = []
    lines = content.splitlines()

    current_title = ""

    for line in lines:
        line_normalised = line.replace("#EXTINF:-1,", "#EXTINF:-1").strip()

        if line.startswith("#EXTINF:"):
            current_title = _parse_extinf_line(line_normalised, site.title_filter)
        elif check_valid_ace_url(line_normalised) and current_title:
            ace_stream = _create_ace_stream_from_url(line_normalised, current_title)
            if ace_stream:
                found_streams.append(ace_stream)
                current_title = ""  # Reset after successful match

    return found_streams


def _get_site_content(site: ScrapeSiteIPTV) -> str | None:
    """Get site content from cache or by scraping."""
    cached_content = scraper_cache.load_from_cache(site.url)

    if scraper_cache.is_cache_valid(site.url):
        return cached_content

    logger.debug("Scraping streams from IPTV site: %s", site)
    try:
        response = requests.get(site.url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        error_short = type(e).__name__
        logger.error("Error scraping IPTV site %s, %s", site.url, error_short)  # noqa: TRY400
        return None

    response.encoding = "utf-8"
    content = response.text
    scraper_cache.save_to_cache(site.url, content)

    return content


def scrape_streams_iptv_site(site: ScrapeSiteIPTV) -> FoundAceStreams | None:
    """Scrape the streams from the configured IPTV sites."""
    content = _get_site_content(site)
    if not content:
        return None

    found_streams = _parse_m3u_content(content, site)

    logger.debug("Found %d streams on IPTV site %s", len(found_streams), site.name)

    return (
        FoundAceStreams(
            site_name=site.name,
            site_slug=site.slug,
            stream_list=found_streams,
        )
        if found_streams
        else None
    )
