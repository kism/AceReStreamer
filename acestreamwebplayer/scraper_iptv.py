"""Scraper for IPTV sites to find AceStream streams."""

import requests

from .config import ScrapeSiteIPTV
from .logger import get_logger
from .scraper_objects import FoundAceStream, FoundAceStreams

logger = get_logger(__name__)


def scrape_streams_iptv_sites(sites: list[ScrapeSiteIPTV], disallowed_words: list[str]) -> list[FoundAceStreams]:
    """Scrape the streams from the configured IPTV sites."""
    found_streams: list[FoundAceStreams] = []

    for site in sites:
        streams = scrape_streams_iptv_site(site, disallowed_words)
        if streams:
            found_streams.append(streams)

    return found_streams


def scrape_streams_iptv_site(site: ScrapeSiteIPTV, disallowed_words: list[str]) -> FoundAceStreams | None:
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

    ace_url_prefix = "http://127.0.0.1:6878/ace/getstream?id="
    url_section = 2

    lines = response.text.splitlines()
    title = ""
    ace_id = ""
    for line in lines:
        if line.startswith("#EXTINF:"):
            ace_id = ""  # Reset
            title = ""  # Reset
            parts = line.split(",")
            if len(parts) < url_section:
                logger.warning("Malformed line in IPTV stream: %s", line)
                continue

            title = parts[1].strip()
        elif line.startswith(ace_url_prefix):
            ace_id = line.split(ace_url_prefix)[-1].strip()
            ace_id = ace_id.split("&")[0]  # Remove any query parameters if present

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
            stream_list=[stream for stream in streams if not any(word in stream.title for word in disallowed_words)],
        )
        if streams
        else None
    )
