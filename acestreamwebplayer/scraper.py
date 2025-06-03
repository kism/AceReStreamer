"""Scraper object."""

import re

import requests
from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel

from .logger import get_logger
from .config import ScrapeSite

logger = get_logger(__name__)


class FoundAceStream(BaseModel):
    """Model for a found AceStream."""

    title: str
    url: str


class FoundAceStreams(BaseModel):
    """Model for a list of found AceStreams."""

    site: str
    stream_list: list[FoundAceStream]


class CandidateAceStream(BaseModel):
    """Model for a candidate AceStream."""

    url: str
    title_candidates: list[str] = []


# KISM-BOILERPLATE: Demo object, doesn't do much
class AceScraper:
    """Demo object."""

    def __init__(self, site_list: list[ScrapeSite]) -> None:
        """Init MyCoolObject."""
        self.site_list = site_list
        self.streams: list[FoundAceStreams] = []
        for site in self.site_list:
            found_ace_streams = self._scrape_streams(site)
            if found_ace_streams:
                self.streams.append(found_ace_streams)

    def _cleanup_candidate_title(self, title: str) -> str:
        """Cleanup the candidate title."""
        title = title.strip()
        title = title.split("acestream://")[-1].strip()
        title = title.split("\n")[0].strip()  # Remove any newlines
        # Remove any ace 40 digit hex ids from the title
        return re.sub(r"\b[0-9a-fA-F]{40}\b", "", title).strip()

    def _scrape_streams(self, site: ScrapeSite) -> FoundAceStreams | None:
        """Scrape the streams from the configured sites."""
        streams_candidates: list[CandidateAceStream] = []

        logger.debug("Scraping streams from site: %s", site)
        try:
            response = requests.get(site.url, timeout=10)
            response.raise_for_status()

        except requests.RequestException as e:
            logger.exception("Error scraping site %s: %s", site, e)
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        def search_for_candidate(
            candidate_titles: list[str], target_html_class: str = "", html_tag: Tag | None = None
        ) -> list[str]:
            """Search the parent of the given tag for a title."""
            if not html_tag or not isinstance(html_tag, Tag):
                return candidate_titles

            html_classes = html_tag.get("class", None)
            if not html_classes:
                return candidate_titles

            # Search children
            more = search_for_candidate(
                candidate_titles=candidate_titles,
                target_html_class=target_html_class,
                html_tag=html_tag.child,
            )
            candidate_titles.extend(more)

            # Search Parents
            more = search_for_candidate(
                candidate_titles=candidate_titles,
                target_html_class=target_html_class,
                html_tag=html_tag.parent,
            )
            candidate_titles.extend(more)

            # Search the current tag
            for html_class in html_classes:
                if html_class == target_html_class:
                    logger.debug("Found class: %s", html_class)
                    candidate_title = self._cleanup_candidate_title(html_tag.get_text())
                    logger.warning("WE ADDING A TITLE: %s", candidate_title)
                    candidate_titles.append(candidate_title)

            return candidate_titles

        for link in soup.find_all("a", href=True):
            if "acestream://" in link["href"]:
                ace_stream_url: str = link["href"]

                candidate_titles: list[str] = []

                # tags_to_search = [link]

                # if link.parent and isinstance(link.parent, Tag):
                #     tags_to_search.append(link.parent)

                #     if link.parent.parent and isinstance(link.parent.parent, Tag):
                #         tags_to_search.append(link.parent.parent)


                # for tag in tags_to_search:
                #     if isinstance(tag, Tag):
                #         candidate_titles.extend(
                #             search_for_candidate(
                #                 candidate_titles=candidate_titles.copy(),
                #                 target_html_class=site.html_class,
                #                 html_tag=tag,
                #             )
                #         )

                # Recurse through the parent tags to find a suitable title
                candidate_titles.extend(
                    search_for_candidate(
                        candidate_titles=candidate_titles.copy(),
                        target_html_class=site.html_class,
                        html_tag=link.parent,
                    )
                )

                logger.info("Part 1 complete, n found: %s", len(candidate_titles))

                # Recursively search the previous sibling for a title
                previous_sibling = link.find_previous_sibling()
                if previous_sibling and isinstance(previous_sibling, Tag):
                    candidate_titles.extend(
                        search_for_candidate(
                            candidate_titles=candidate_titles.copy(),
                            target_html_class=site.html_class,
                            html_tag=previous_sibling,
                        )
                    )

                logger.info("Part 2 complete, n found: %s", len(candidate_titles))

                # Finally, do the same for the parent's sibling
                if link.parent:
                    parent_sibling = link.parent.find_previous_sibling()
                    if parent_sibling and isinstance(parent_sibling, Tag):
                        candidate_titles.extend(
                            search_for_candidate(
                                candidate_titles=candidate_titles.copy(),
                                target_html_class=site.html_class,
                                html_tag=parent_sibling,
                            )
                        )

                logger.info("Part 3 complete, n found: %s", len(candidate_titles))

                logger.info(candidate_titles)

                streams_candidates.append(
                    CandidateAceStream(
                        url=ace_stream_url,
                        title_candidates=list(set(candidate_titles)),  # Remove duplicates
                    )
                )

        found_streams = self._process_candidates(streams_candidates)
        return FoundAceStreams(
            site=site.name,
            stream_list=found_streams,
        )

    def _process_candidates(self, candidates: list[CandidateAceStream]) -> list[FoundAceStream]:
        """Process candidate streams to find valid AceStreams."""
        found_streams: list[FoundAceStream] = []

        all_titles = []

        for candidate in candidates:
            all_titles.extend(candidate.title_candidates)

        for candidate in candidates:
            new_title_candidates = []
            for title in candidate.title_candidates:
                logger.debug("Processing title candidate: %s", title)
                title_count = all_titles.count(title)
                if title_count == 1:
                    # If the title appears only once, it's likely a unique title
                    new_title_candidates.append(title)

            title = "<Unknown Title>"
            if len(new_title_candidates) == 1:
                title = new_title_candidates[0]
            elif len(new_title_candidates) > 1:
                # If there are multiple candidates, we can choose the first one
                title = " / ".join(new_title_candidates)

            url_no_uri = candidate.url.split("acestream://")[-1].strip()

            found_streams.append(
                FoundAceStream(
                    title=title,
                    url=url_no_uri,
                )
            )

        logger.debug("Streams: \n%s", "\n".join([f"{stream.title} - {stream.url}" for stream in found_streams]))

        return found_streams
