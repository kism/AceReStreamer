"""Helper functions and functions for searching in beautiful soup tags."""

from datetime import timedelta

import requests
from bs4 import BeautifulSoup, Tag

from ._obj_instances import scraper_cache
from .config import ScrapeSiteHTML
from .helpers import check_valid_ace_id
from .logger import get_logger
from .scraper_helpers import (
    STREAM_TITLE_MAX_LENGTH,
    candidates_regex_cleanup,
    check_title_allowed,
    check_valid_ace_url,
    cleanup_candidate_title,
    extract_ace_id_from_url,
    get_tvg_id_from_title,
)
from .scraper_objects import CandidateAceStream, FoundAceStream, FoundAceStreams

logger = get_logger(__name__)


def scrape_streams_html_sites(sites: list[ScrapeSiteHTML]) -> list[FoundAceStreams]:
    """Scrape the streams from the configured sites."""
    found_streams: list[FoundAceStreams] = []

    for site in sites:
        streams = scrape_streams_html_site(site)
        if streams:
            found_streams.append(streams)

    return found_streams


def scrape_streams_html_site(site: ScrapeSiteHTML) -> FoundAceStreams | None:
    """Scrape the streams from the configured sites."""
    streams_candidates: list[CandidateAceStream] = []
    cache_max_age = timedelta(hours=1)  # HTML Sources we need to scrape more often

    scraped_site_str = scraper_cache.load_from_cache(site.url)

    if not scraper_cache.is_cache_valid(site.url, cache_max_age):
        logger.debug("Scraping streams from site: %s", site)
        try:
            response = requests.get(site.url, timeout=10)
            response.raise_for_status()
            response.encoding = "utf-8"  # Ensure the response is decoded correctly
            scraped_site_str = response.text
            scraper_cache.save_to_cache(site.url, scraped_site_str)
        except requests.RequestException as e:
            error_short = type(e).__name__
            logger.error("Error scraping site %s, %s", site.url, error_short)  # noqa: TRY400 Naa this should be shorter
            return None

    soup = BeautifulSoup(scraped_site_str, "html.parser")

    for link in soup.find_all("a", href=True):
        # Appease mypy
        if not isinstance(link, Tag):
            continue
        link_href = link.get("href", None)
        if not link_href or not isinstance(link_href, str):
            continue

        # We are iterating through all links, we only want AceStream links
        if check_valid_ace_url(link_href):
            candidate_titles: list[str] = []
            ace_stream_url: str = link_href.strip()

            # Skip URLs that are already added, maybe this can check if the second instance has a different title
            if ace_stream_url in [stream.ace_id for stream in streams_candidates]:
                continue

            # Recurse through the parent tags to find a suitable title
            candidate_titles.extend(
                _search_for_candidate(
                    candidate_titles=candidate_titles.copy(),
                    target_html_class=site.target_class,
                    html_tag=link,
                )
            )

            # Recurse through parent tags and check their siblings for a suitable title
            if site.check_sibling:
                candidate_titles.extend(
                    _search_sibling_for_candidate(
                        candidate_titles=candidate_titles.copy(),
                        target_html_class=site.target_class,
                        html_tag=link,
                    )
                )

            # Through all title candidates, clean them up if there is a regex defined
            candidate_titles = candidates_regex_cleanup(
                candidate_titles,
                site.title_filter.regex_postprocessing,
            )

            candidate_titles = list(set(candidate_titles))  # Remove duplicates

            streams_candidates.append(
                CandidateAceStream(
                    ace_id=ace_stream_url,
                    title_candidates=candidate_titles,
                )
            )

    found_streams = process_candidates(streams_candidates, site)
    return FoundAceStreams(
        site_name=site.name,
        site_slug=site.slug,
        stream_list=found_streams,
    )


def process_candidates(candidates: list[CandidateAceStream], site: ScrapeSiteHTML) -> list[FoundAceStream]:
    """Process candidate streams to find valid AceStreams."""
    found_streams: list[FoundAceStream] = []

    all_titles = []

    # Collect a list of all candidate titles to find duplicates including duplicates
    for candidate in candidates:
        all_titles.extend(candidate.title_candidates)

    for candidate in candidates:
        new_title_candidates = []
        for title in candidate.title_candidates:
            new_title = title
            # Anything that gets found for every candidate gets ignored
            if all_titles.count(title) >= len(candidates):
                continue

            if len(title) > STREAM_TITLE_MAX_LENGTH:
                new_title = title[:STREAM_TITLE_MAX_LENGTH]  # Shorten titles if they are too long

            new_title_candidates.append(new_title)

        title = "<Unknown Title>"

        if len(new_title_candidates) == 1:
            title = new_title_candidates[0]
        elif len(new_title_candidates) > 1:
            # If there are multiple candidates, we can choose the first one
            title = " / ".join(new_title_candidates)

        url_no_uri = extract_ace_id_from_url(candidate.ace_id)

        if not check_title_allowed(
            title=title,
            title_filter=site.title_filter,
        ):
            continue

        if not check_valid_ace_id(url_no_uri):
            logger.warning("Invalid Ace ID found in candidate: %s, skipping", url_no_uri)
            continue

        tvg_id = get_tvg_id_from_title(title)

        found_streams.append(
            FoundAceStream(
                title=title,
                ace_id=url_no_uri,
                tvg_id=tvg_id,
            )
        )

    logger.debug("Found %d streams on site %s", len(found_streams), site.name)

    return found_streams


def _check_candidate(target_html_class: str, html_tag: Tag | None) -> list[str]:
    """Check if the tag has the target class."""
    if not html_tag or not isinstance(html_tag, Tag):
        return []
    html_classes = html_tag.get("class", None)

    html_classes_good = [""] if not html_classes or not isinstance(html_classes, list) else html_classes

    candidate_titles: list[str] = []
    for html_class in html_classes_good:
        if html_class == target_html_class:
            candidate_title = cleanup_candidate_title(html_tag.get_text())
            candidate_titles.append(candidate_title)

    return candidate_titles


def _search_for_candidate(
    candidate_titles: list[str], target_html_class: str = "", html_tag: Tag | None = None
) -> list[str]:
    """Search the parent of the given tag for a title."""
    if not html_tag or not isinstance(html_tag, Tag):
        return candidate_titles

    # Search Parents
    more = _search_for_candidate(
        candidate_titles=candidate_titles,
        target_html_class=target_html_class,
        html_tag=html_tag.parent,
    )
    candidate_titles.extend(more)

    if target_html_class != "":
        html_classes = html_tag.get("class", None)
        if not html_classes:
            return candidate_titles

    # Search Self
    candidates = _check_candidate(target_html_class, html_tag)
    candidate_titles.extend(candidates)

    return candidate_titles


def _search_sibling_for_candidate(
    candidate_titles: list[str], target_html_class: str = "", html_tag: Tag | None = None
) -> list[str]:
    """Search the previous sibling of the given tag for a title."""
    if not html_tag or not isinstance(html_tag, Tag):
        return candidate_titles

    # Recurse through the parent tags
    more = _search_sibling_for_candidate(
        candidate_titles=candidate_titles.copy(),
        target_html_class=target_html_class,
        html_tag=html_tag.parent,
    )
    candidate_titles.extend(more)

    # Find and search previous sibling
    previous_sibling = html_tag.find_previous_sibling()
    if previous_sibling and isinstance(previous_sibling, Tag):
        more = _check_candidate(target_html_class, previous_sibling)
        candidate_titles.extend(more)

    return candidate_titles
