"""Scraper for IPTV sites to find AceStream streams."""

import requests

from .config import ScrapeSiteIPTV
from .logger import get_logger
from .scraper_cache import ScraperCache
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
    scraper_cache = ScraperCache()
    found_streams: list[FoundAceStream] = []

    scraped_site_str = scraper_cache.load_from_cache(site.url)

    if not scraper_cache.is_cache_valid(site.url):
        logger.debug("Scraping streams from IPTV site: %s", site)
        try:
            response = requests.get(site.url, timeout=10)
            response.raise_for_status()
            response.encoding = "utf-8"  # Ensure the response is decoded correctly
            scraped_site_str = response.text
            scraper_cache.save_to_cache(site.url, scraped_site_str)
        except requests.RequestException as e:
            error_short = type(e).__name__
            logger.error("Error scraping IPTV site %s, %s", site.url, error_short)  # noqa: TRY400 Naa this should be shorter
            return None

    url_section = 2

    lines = scraped_site_str.splitlines()
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
            found_streams.append(
                FoundAceStream(
                    title=title,
                    ace_id=ace_id,
                )
            )

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
