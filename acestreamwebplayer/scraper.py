"""Scraper object."""

import re

import requests
from bs4 import BeautifulSoup
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
        streams_candidates = []

        logger.debug("Scraping streams from site: %s", site)
        try:
            response = requests.get(site.url, timeout=10)
            response.raise_for_status()

        except requests.RequestException as e:
            logger.exception("Error scraping site %s: %s", site, e)
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Determine search scope based on html_class configuration
        if site.html_class != "":
            search_scope = soup.find_all(class_=site.html_class)
            if not search_scope:
                logger.warning(
                    "No elements found with class '%s' on site %s",
                    site.html_class,
                    site.name,
                )
                return FoundAceStreams(site=site.name, stream_list=[])
            logger.debug(
                "Found %d elements with class '%s' on site %s",
                len(search_scope),
                site.html_class,
                site.name,
            )
            for element in search_scope:
                logger.debug("Element found: %s", element)
        else:
            search_scope = [soup]

        # Search for acestream links within the determined scope
        for scope in search_scope:
            for link in scope.find_all("a", href=True):
                if "acestream://" in link["href"]:
                    title_candidates = []
                    ace_stream_url: str = link["href"]

                    if link.text:
                        title_candidates.append(self._cleanup_candidate_title(link.text))
                    # Look for Text in parent divs or spans

                    parent_divs = link.find_parents(["div", "span"])
                    for parent in parent_divs:
                        # Get direct text content (not from nested tags)
                        if parent.string:
                            title_candidates.append(self._cleanup_candidate_title(parent.string))

                        # Get text from direct child text nodes only
                        for text_node in parent.find_all(text=True, recursive=False):
                            logger.info("Found text node: %s", text_node)
                            if text_node.strip():
                                title_candidates.append(self._cleanup_candidate_title(text_node.strip()))

                        # Get text from immediate previous sibling only
                        prev_sibling = parent.find_previous_sibling(["div", "span"])
                        if prev_sibling:
                            if prev_sibling.string:
                                title_candidates.append(self._cleanup_candidate_title(prev_sibling.string))
                            for text_node in prev_sibling.find_all(text=True, recursive=False):
                                if text_node.strip():
                                    title_candidates.append(self._cleanup_candidate_title(text_node.strip()))

                    # Remove duplicates and empty titles
                    title_candidates = list(set(title_candidates))

                    # Create a CandidateAceStream object
                    streams_candidates.append(CandidateAceStream(url=ace_stream_url, title_candidates=title_candidates))

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
