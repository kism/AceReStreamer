"""Helper functions and functions for searching in beautiful soup tags."""

from datetime import timedelta
from typing import TYPE_CHECKING

import requests
from bs4 import BeautifulSoup, Tag

from acerestreamer.instances_mapping import category_xc_category_id_mapping
from acerestreamer.utils import check_valid_content_id_or_infohash
from acerestreamer.utils.logger import get_logger

from .common import ScraperCommon
from .models import CandidateAceStream, FoundAceStream

if TYPE_CHECKING:
    from acerestreamer.config import ScrapeSiteHTML
else:
    ScrapeSiteHTML = object

logger = get_logger(__name__)


class HTTPStreamScraper(ScraperCommon):
    """Scraper for websites to find AceStream streams."""

    def scrape_sites(self, sites: list[ScrapeSiteHTML]) -> list[FoundAceStream]:
        """Scrape the streams from the configured sites."""
        found_streams: list[FoundAceStream] = []

        for site in sites:
            streams = self._scrape_site(site)
            if streams:
                found_streams.extend(streams)

        return found_streams

    def _scrape_site(self, site: ScrapeSiteHTML) -> list[FoundAceStream]:
        """Scrape the streams from the configured sites."""
        streams_candidates: list[CandidateAceStream] = []
        cache_max_age = timedelta(hours=1)  # HTML Sources we need to scrape more often

        scraped_site_str = self.scraper_cache.load_from_cache(site.url)

        if not self.scraper_cache.is_cache_valid(site.url, cache_max_age):
            logger.debug("Scraping streams from site: %s", site)
            try:
                response = requests.get(site.url, timeout=10)
                response.raise_for_status()
                response.encoding = "utf-8"  # Ensure the response is decoded correctly
                scraped_site_str = response.text
                self.scraper_cache.save_to_cache(site.url, scraped_site_str)
            except requests.RequestException as e:
                error_short = type(e).__name__
                logger.error("Error scraping site %s, %s", site.url, error_short)  # noqa: TRY400 Short error for requests
                return []

        soup = BeautifulSoup(scraped_site_str, "html.parser")

        for link in soup.find_all("a", href=True):
            # Appease mypy
            if not isinstance(link, Tag):
                continue
            link_href = link.get("href", None)
            if not link_href or not isinstance(link_href, str):
                continue

            # We are iterating through all links, we only want AceStream links
            if self.name_processor.check_valid_ace_url(link_href):
                candidate_titles: list[str] = []
                ace_stream_url: str = link_href.strip()

                # Skip URLs that are already added, maybe this can check if the second instance has a different title
                if ace_stream_url in [stream.content_id for stream in streams_candidates]:
                    continue

                # Recurse through the parent tags to find a suitable title
                candidate_titles.extend(
                    self._search_for_candidate(
                        candidate_titles=candidate_titles.copy(),
                        target_html_class=site.target_class,
                        html_tag=link,
                    )
                )

                # Recurse through parent tags and check their siblings for a suitable title
                if site.check_sibling:
                    candidate_titles.extend(
                        self._search_sibling_for_candidate(
                            candidate_titles=candidate_titles.copy(),
                            target_html_class=site.target_class,
                            html_tag=link,
                        )
                    )

                # Through all title candidates, clean them up if there is a regex defined
                candidate_titles = self.name_processor.candidates_regex_cleanup(
                    candidate_titles,
                    site.title_filter.regex_postprocessing,
                )

                candidate_titles = list(set(candidate_titles))  # Remove duplicates

                streams_candidates.append(
                    CandidateAceStream(
                        content_id=ace_stream_url,
                        title_candidates=candidate_titles,
                    )
                )

        return self._process_candidates(streams_candidates, site)

    def _process_candidates(self, candidates: list[CandidateAceStream], site: ScrapeSiteHTML) -> list[FoundAceStream]:
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

                new_title = self.name_processor.trim_title(title)

                new_title_candidates.append(new_title)

            title = "<Unknown Title>"

            if len(new_title_candidates) == 1:
                title = new_title_candidates[0]
            elif len(new_title_candidates) > 1:
                # If there are multiple candidates, we can choose the first one
                title = " / ".join(new_title_candidates)

            content_id = self.name_processor.extract_content_id_from_url(candidate.content_id)

            if not self.name_processor.check_title_allowed(
                title=title,
                title_filter=site.title_filter,
            ):
                continue

            if not check_valid_content_id_or_infohash(content_id):
                logger.warning("Invalid Ace ID found in candidate: %s, skipping", content_id)
                continue

            tvg_id = self.name_processor.get_tvg_id_from_title(title)

            tvg_logo = self.name_processor.find_tvg_logo_image(title)

            group_title = self.name_processor.populate_group_title(
                group_title="",
                title=title,
            )
            category_xc_category_id_mapping.get_xc_category_id(group_title)  # Populate

            found_streams.append(
                FoundAceStream(
                    title=title,
                    content_id=content_id,
                    tvg_id=tvg_id,
                    tvg_logo=tvg_logo,
                    group_title=group_title,
                    site_names=[site.name],
                )
            )

        logger.debug("Found %d streams on site %s", len(found_streams), site.name)

        return found_streams

    def _check_candidate(self, target_html_class: str, html_tag: Tag | None) -> list[str]:
        """Check if the tag has the target class."""
        if not html_tag or not isinstance(html_tag, Tag):
            return []
        html_classes = html_tag.get("class", None)

        html_classes_good = [""] if not html_classes or not isinstance(html_classes, list) else html_classes

        candidate_titles: list[str] = []
        for html_class in html_classes_good:
            if html_class == target_html_class:
                candidate_title = self.name_processor.cleanup_candidate_title(html_tag.get_text())
                candidate_titles.append(candidate_title)

        return candidate_titles

    def _search_for_candidate(
        self, candidate_titles: list[str], target_html_class: str = "", html_tag: Tag | None = None
    ) -> list[str]:
        """Search the parent of the given tag for a title."""
        if not html_tag or not isinstance(html_tag, Tag):
            return candidate_titles

        # Search Parents
        more = self._search_for_candidate(
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
        candidates = self._check_candidate(target_html_class, html_tag)
        candidate_titles.extend(candidates)

        return candidate_titles

    def _search_sibling_for_candidate(
        self, candidate_titles: list[str], target_html_class: str = "", html_tag: Tag | None = None
    ) -> list[str]:
        """Search the previous sibling of the given tag for a title."""
        if not html_tag or not isinstance(html_tag, Tag):
            return candidate_titles

        # Recurse through the parent tags
        more = self._search_sibling_for_candidate(
            candidate_titles=candidate_titles.copy(),
            target_html_class=target_html_class,
            html_tag=html_tag.parent,
        )
        candidate_titles.extend(more)

        # Find and search previous sibling
        previous_sibling = html_tag.find_previous_sibling()
        if previous_sibling and isinstance(previous_sibling, Tag):
            more = self._check_candidate(target_html_class, previous_sibling)
            candidate_titles.extend(more)

        return candidate_titles
