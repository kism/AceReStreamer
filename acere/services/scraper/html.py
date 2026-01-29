"""Helper functions and functions for searching in beautiful soup tags."""

from collections import Counter
from datetime import timedelta
from typing import TYPE_CHECKING

import aiohttp
from bs4 import BeautifulSoup, Tag

from acere.utils.exception_handling import log_aiohttp_exception
from acere.utils.helpers import check_valid_content_id_or_infohash
from acere.utils.logger import get_logger

from . import name_processor
from .common import ScraperCommon
from .models import CandidateAceStream, FoundAceStream

if TYPE_CHECKING:
    from acere.core.config.scraper import ScrapeSiteHTML
else:
    ScrapeSiteHTML = object

logger = get_logger(__name__)

HTML_CACHE_MAX_AGE = timedelta(hours=1)  # HTML Sources we need to scrape more often


class HTMLStreamScraper(ScraperCommon):
    """Scraper for websites to find AceStream streams."""

    async def scrape_sites(self, sites: list[ScrapeSiteHTML]) -> list[FoundAceStream]:
        """Scrape the streams from the configured sites."""
        found_streams: list[FoundAceStream] = []

        for site in sites:
            streams = await self._scrape_site(site)
            if streams:
                found_streams.extend(streams)

        return found_streams

    async def _scrape_site(self, site: ScrapeSiteHTML) -> list[FoundAceStream]:
        """Scrape the streams from the configured sites."""
        streams_candidates: list[CandidateAceStream] = []
        cache_max_age = HTML_CACHE_MAX_AGE

        scraped_site_str = self.scraper_cache.load_from_cache(site.url)

        if not self.scraper_cache.is_cache_valid(site.url, cache_max_age):
            logger.info("Scraping streams from HTML site: %s", site.name)
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(site.url.encoded_string()) as response:
                        response.raise_for_status()
                        scraped_site_str = await response.text()

            except (aiohttp.ClientError, TimeoutError) as e:
                log_aiohttp_exception(logger, site.url, e)
                return []
        else:
            logger.debug("Loaded HTML site content from cache for: %s", site.name)

        logger.debug("Caching HTML site content for: %s", site.name)
        self.scraper_cache.save_to_cache(site.url, scraped_site_str)

        logger.debug("Parsing HTML for site: %s", site.name)
        soup = BeautifulSoup(scraped_site_str, "html.parser")

        for link in soup.find_all("a", href=True):
            # Appease mypy
            if not isinstance(link, Tag):
                continue
            link_href = link.get("href", None)
            if not link_href or not isinstance(link_href, str):
                continue

            # We are iterating through all links, we only want AceStream links
            valid_ace_uri = name_processor.check_valid_ace_uri(link_href)

            if valid_ace_uri is not None:
                candidate_titles: list[str] = []

                # Skip URLs that are already added, maybe this can check if the second instance has a different title
                if valid_ace_uri in [stream.ace_uri for stream in streams_candidates]:
                    continue

                # Recurse through the parent tags to find a suitable title
                candidate_titles.extend(
                    self._search_for_candidate(
                        candidate_titles=candidate_titles.copy(),
                        target_html_class=site.html_filter.target_class,
                        html_tag=link,
                    )
                )

                # Recurse through parent tags and check their siblings for a suitable title
                if site.html_filter.check_sibling:
                    candidate_titles.extend(
                        self._search_sibling_for_candidate(
                            candidate_titles=candidate_titles.copy(),
                            target_html_class=site.html_filter.target_class,
                            html_tag=link,
                        )
                    )

                # Through all title candidates, clean them up if there is a regex defined
                candidate_titles = name_processor.candidates_regex_cleanup(
                    candidate_titles,
                    site.title_filter.regex_postprocessing,
                )

                candidate_titles = list(set(candidate_titles))  # Remove duplicates

                streams_candidates.append(
                    CandidateAceStream(
                        ace_uri=valid_ace_uri,
                        title_candidates=candidate_titles,
                    )
                )

            else:
                logger.trace("Skipping non-AceStream link: %s", link_href)

        return self._process_candidates(streams_candidates, site)

    def _process_candidates(self, candidates: list[CandidateAceStream], site: ScrapeSiteHTML) -> list[FoundAceStream]:  # noqa: C901 Separated out the best title logic
        """Process candidate streams to find valid AceStreams."""
        found_streams: list[FoundAceStream] = []

        # All titles and their counts
        all_titles: Counter[str] = Counter()
        for candidate in candidates:
            all_titles.update(candidate.title_candidates)

        max_count = max(all_titles.values()) if all_titles else 0
        max_count_common_on_all = max_count == len(candidates)
        total_candidates = len(candidates)

        def _select_best_title(
            candidate: CandidateAceStream,
            content_id: str,
        ) -> str:
            """Select the best title candidates based on match strength."""
            title = content_id  # Default to content_id if no title found
            new_title_candidates: list[str] = []
            lowest_duplicate_count = (
                min(all_titles[title] for title in candidate.title_candidates) if candidate.title_candidates else 0
            )
            best_strength = 0

            for title in candidate.title_candidates:
                match_strength = -1
                if all_titles[title] == 1:  # Unique title, most trustworthy
                    match_strength = 3
                elif (
                    site.html_filter.target_class != "" and all_titles[title] == lowest_duplicate_count
                ):  # We have a target class, more trustworthy
                    match_strength = 2
                elif (
                    (all_titles[title] != max_count and not max_count_common_on_all) or total_candidates == 1
                ):  # If the title is not common to all candidates, or we only have one candidate
                    match_strength = 1

                if match_strength > best_strength:
                    new_title_candidates = []  # We have done better, reset candidates
                    best_strength = match_strength

                if match_strength >= best_strength:  # We are okay with more candidates of the same strength
                    new_title = name_processor.trim_title(title)
                    new_title_candidates.append(new_title)

            for title in new_title_candidates:
                title.strip()

            if len(new_title_candidates) == 1:
                title = new_title_candidates[0]
            elif len(new_title_candidates) > 1:
                # If there are multiple candidates, join them with a separator
                title = " / ".join(new_title_candidates)

            return title

        for candidate in candidates:
            content_id = name_processor.extract_content_id_from_url(candidate.ace_uri)

            if not check_valid_content_id_or_infohash(content_id):
                logger.warning("Invalid Ace ID found in candidate: %s, skipping", content_id)
                continue

            override_title = name_processor.get_title_override_from_content_id(content_id)
            title = override_title or _select_best_title(candidate, content_id)

            if not name_processor.check_title_allowed(
                title=title,
                title_filter=site.title_filter,
            ):
                continue

            # Okay we are good to add
            tvg_id = name_processor.get_tvg_id_from_title(title)
            tvg_logo = name_processor.find_tvg_logo_image(title)
            group_title = name_processor.populate_group_title(
                group_title="",
                title=title,
            )

            found_streams.append(
                FoundAceStream(
                    title=title,
                    content_id=content_id,
                    tvg_id=tvg_id,
                    tvg_logo=tvg_logo,
                    group_title=group_title,
                    sites_found_on=[site.name],
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
                candidate_title = name_processor.cleanup_candidate_title(html_tag.get_text())
                candidate_titles.append(candidate_title)

        return candidate_titles

    def _search_for_candidate(
        self,
        candidate_titles: list[str],
        target_html_class: str = "",
        html_tag: Tag | None = None,
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
            logger.trace("Checking HTML classes: %s for target: %s", html_classes, target_html_class)
            if not html_classes:
                return candidate_titles

        # Search Self
        candidates = self._check_candidate(target_html_class, html_tag)
        candidate_titles.extend(candidates)

        return candidate_titles

    def _search_sibling_for_candidate(
        self,
        candidate_titles: list[str],
        target_html_class: str = "",
        html_tag: Tag | None = None,
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
