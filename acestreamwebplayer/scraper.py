"""Scraper object."""

import requests
from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel

from .config import ScrapeSite
from .logger import get_logger
from .scraper_helpers import search_for_candidate, search_sibling_for_candidate

logger = get_logger(__name__)

STREAM_TITLE_MAX_LENGTH = 30


class FoundAceStream(BaseModel):
    """Model for a found AceStream."""

    title: str
    url: str


class FoundAceStreams(BaseModel):
    """Model for a list of found AceStreams."""

    site_name: str
    stream_list: list[FoundAceStream]


class CandidateAceStream(BaseModel):
    """Model for a candidate AceStream."""

    url: str
    title_candidates: list[str] = []


class AceScraper:
    """Scraper object."""

    def __init__(self, site_list: list[ScrapeSite]) -> None:
        """Init MyCoolObject."""
        self.site_list = site_list
        self.streams: list[FoundAceStreams] = []
        for site in self.site_list:
            found_ace_streams = self._scrape_streams(site)
            if found_ace_streams:
                self.streams.append(found_ace_streams)

        self.print_streams()

    def get_streams(self) -> list[dict[str, str]]:
        """Get the found streams as a list of JSON strings."""
        return [stream.model_dump() for stream in self.streams]

    def print_streams(self) -> None:
        """Print the found streams."""
        msg = "Found AceStreams:\n"
        for found_streams in self.streams:
            msg += f"Site: {found_streams.site_name}\n"
            for stream in found_streams.stream_list:
                msg += f"  - {stream.title} ({stream.url})\n"
        logger.info(msg)

    def _scrape_streams(self, site: ScrapeSite) -> FoundAceStreams | None:
        """Scrape the streams from the configured sites."""
        streams_candidates: list[CandidateAceStream] = []

        logger.debug("Scraping streams from site: %s", site)
        try:
            response = requests.get(site.url, timeout=10)
            response.raise_for_status()
            response.encoding = "utf-8"  # Ensure the response is decoded correctly
        except requests.RequestException as e:
            logger.exception("Error scraping site %s: %s", site, e)
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            # Appease mypy
            if not isinstance(link, Tag):
                continue
            link_href = link.get("href", None)
            if not link_href or not isinstance(link_href, str):
                continue

            # We are iterating through all links, we only want AceStream links
            if "acestream://" in link_href:
                candidate_titles: list[str] = []
                ace_stream_url: str = link_href.strip()

                # Skip URLs that are already added, maybe this can check if the second instance has a different title
                if ace_stream_url in [stream.url for stream in streams_candidates]:
                    continue

                # Recurse through the parent tags to find a suitable title
                candidate_titles.extend(
                    search_for_candidate(
                        candidate_titles=candidate_titles.copy(),
                        target_html_class=site.html_class,
                        html_tag=link,
                    )
                )

                # Recurse through parent tags and check their siblings for a suitable title
                if site.check_sibling:
                    candidate_titles.extend(
                        search_sibling_for_candidate(
                            candidate_titles=candidate_titles.copy(),
                            target_html_class=site.html_class,
                            html_tag=link,
                        )
                    )

                # Create a candidate AceStream with the found titles, remove duplicates
                streams_candidates.append(
                    CandidateAceStream(
                        url=ace_stream_url,
                        title_candidates=list(set(candidate_titles)),
                    )
                )

        found_streams = self._process_candidates(streams_candidates)
        return FoundAceStreams(
            site_name=site.name,
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
                new_title = title
                if len(title) < STREAM_TITLE_MAX_LENGTH:
                    new_title = title[
                        -STREAM_TITLE_MAX_LENGTH:
                    ]  # Shorten titles to last 20 characters if they are too short

                new_title_candidates.append(new_title)

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
