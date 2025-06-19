"""Scraper for IPTV sites to find AceStream streams."""

import requests

from .config import ScrapeSiteIPTV
from .logger import get_logger
from .scraper_helpers import check_title_allowed, check_valid_ace_id, check_valid_ace_url, extract_ace_id_from_url
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


def scrape_streams_iptv_site(site: ScrapeSiteIPTV) -> FoundAceStreams | None:
    """Scrape the streams from the configured IPTV sites."""
    streams: list[FoundAceStream] = []

    logger.debug("Scraping streams from IPTV site: %s", site)
    try:
        response = requests.get(site.url, timeout=10)
        response.raise_for_status()
        response.encoding = "utf-8"  # Ensure the response is decoded correctly
    except requests.RequestException as e:
        error_short = type(e).__name__
        logger.error("Error scraping IPTV site %s, %s", site.url, error_short)  # noqa: TRY400 Naa this should be shorter
        return None

    url_section = 2

    lines = response.text.splitlines()
    title = ""
    ace_id = ""
    for line in lines:
        line_normalised = line.replace("#EXTINF:-1,", "#EXTINF:-1").strip()
        if line.startswith("#EXTINF:"):
            ace_id = ""  # Reset
            title = ""  # Reset
            parts = line_normalised.split(",")
            if len(parts) != url_section:
                logger.warning("Malformed line in IPTV stream: %s", line_normalised)
                continue

            title = parts[1].strip()

            if not check_title_allowed(
                title=title,
                title_filter=site.title_filter,
            ):
                title = ""
                continue

        elif check_valid_ace_url(line_normalised):
            ace_id = extract_ace_id_from_url(line_normalised)

            if not check_valid_ace_id(ace_id):
                logger.warning("Invalid Ace ID found in candidate: %s, skipping", ace_id)
                ace_id = ""
                continue

        if title != "" and ace_id != "":
            streams.append(
                FoundAceStream(
                    title=title,
                    ace_id=ace_id,
                )
            )

    logger.debug("Found %d streams on IPTV site %s", len(streams), site.name)

    return (
        FoundAceStreams(
            site_name=site.name,
            site_slug=site.slug,
            stream_list=streams,
        )
        if streams
        else None
    )
