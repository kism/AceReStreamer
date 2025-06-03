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

        response.encoding = "utf-8"  # Ensure the response is decoded correctly

        soup = BeautifulSoup(response.text, "html.parser")

        def check_candidate(target_html_class: str, html_tag: Tag | None) -> list[str]:
            """Check if the tag has the target class."""
            if not html_tag or not isinstance(html_tag, Tag):
                return []
            html_classes = html_tag.get("class", None)
            if not html_classes:
                return []

            candidate_titles: list[str] = []
            for html_class in html_classes:
                if html_class == target_html_class:
                    candidate_title = self._cleanup_candidate_title(html_tag.get_text())
                    candidate_titles.append(candidate_title)

            return candidate_titles

        def search_for_candidate(
            candidate_titles: list[str], target_html_class: str = "", html_tag: Tag | None = None
        ) -> list[str]:
            """Search the parent of the given tag for a title."""
            if not html_tag or not isinstance(html_tag, Tag):
                return candidate_titles

            html_classes = html_tag.get("class", None)
            if not html_classes:
                return candidate_titles

            # Search children could go here with html_tag.child but I think it will do nothing

            # Search Parents
            more = search_for_candidate(
                candidate_titles=candidate_titles,
                target_html_class=target_html_class,
                html_tag=html_tag.parent,
            )
            candidate_titles.extend(more)

            # Search Self
            candidates = check_candidate(target_html_class, html_tag)
            candidate_titles.extend(candidates)

            return candidate_titles

        def search_sibling_for_candidate(
            candidate_titles: list[str], target_html_class: str = "", html_tag: Tag | None = None
        ) -> list[str]:
            """Search the previous sibling of the given tag for a title."""
            if not html_tag or not isinstance(html_tag, Tag):
                return candidate_titles

            # Recurse through the parent tags
            more = search_sibling_for_candidate(
                candidate_titles=candidate_titles.copy(),
                target_html_class=target_html_class,
                html_tag=html_tag.parent,
            )
            candidate_titles.extend(more)

            # Find and search previous sibling
            previous_sibling = html_tag.find_previous_sibling()
            if previous_sibling and isinstance(previous_sibling, Tag):
                more = check_candidate(target_html_class, previous_sibling)
                candidate_titles.extend(more)

            return candidate_titles

        for link in soup.find_all("a", href=True):
            if "acestream://" in link["href"]:
                ace_stream_url: str = link["href"]

                # Skip URLs that are already, maybe this can check if the second instance has a different title
                if ace_stream_url in [stream.url for stream in streams_candidates]:
                    continue

                candidate_titles: list[str] = []

                # Recurse through the parent tags to find a suitable title
                candidate_titles.extend(
                    search_for_candidate(
                        candidate_titles=candidate_titles.copy(),
                        target_html_class=site.html_class,
                        html_tag=link.parent,
                    )
                )

                candidate_titles.extend(
                    search_sibling_for_candidate(
                        candidate_titles=candidate_titles.copy(),
                        target_html_class=site.html_class,
                        html_tag=link.parent,
                    )
                )

                streams_candidates.append(
                    CandidateAceStream(
                        url=ace_stream_url,
                        title_candidates=list(set(candidate_titles)),  # Remove duplicates
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
                if len(title) < 30:
                    new_title = title[-30:]  # Shorten titles to last 20 characters if they are too short

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
