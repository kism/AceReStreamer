"""Scraper object."""

import json

from pathlib import Path

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
    ace_id: str


class FoundAceStreams(BaseModel):
    """Model for a list of found AceStreams."""

    site_name: str
    stream_list: list[FoundAceStream]


class CandidateAceStream(BaseModel):
    """Model for a candidate AceStream."""

    ace_id: str
    title_candidates: list[str] = []


class AceQuality:
    """For tracking quality of Streams."""

    default_quality: int = -1
    quality_on_first_success: int = 20
    min_quality: int = 0
    max_quality: int = 99

    def __init__(self, cache_file: Path | None) -> None:
        """Init AceQuality."""
        self.cache_file = cache_file
        self.ace_streams: dict[str, int] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if self.cache_file and self.cache_file.exists():
            try:
                with self.cache_file.open("r") as f:
                    cache_json_raw = f.read()

                self.ace_streams = json.loads(cache_json_raw)
            except (json.JSONDecodeError, OSError):
                logger.exception("Error loading cache file: %s", self.cache_file)
                return

    def save_cache(self) -> None:
        """Save the current quality cache to a file."""
        logger.debug("Saving AceQuality cache to %s", self.cache_file)
        if not self.cache_file:
            return

        try:
            with self.cache_file.open("w") as f:
                json.dump(self.ace_streams, f, indent=4)
        except OSError:
            logger.exception("Error saving cache file: %s", self.cache_file)

    def get_quality(self, ace_id: str) -> int:
        """Get the quality of a stream by ace_id."""
        if ace_id not in self.ace_streams:
            self.ensure_entry(ace_id)
        return self.ace_streams[ace_id]

    def ensure_entry(self, ace_id: str) -> None:
        """Creates an entry with defaults if it doen't exist."""
        if ace_id not in self.ace_streams:
            self.ace_streams[ace_id] = self.default_quality

    def increment_quality(self, ace_id: str, rating: int) -> None:
        """Increment the quality of a stream by ace_id."""
        logger.debug("Setting quality for AceStream %s by %d", ace_id, rating)
        if ace_id not in self.ace_streams:
            self.ace_streams[ace_id] = self.default_quality

        if self.ace_streams[ace_id] == self.default_quality and rating > 0:
            rating = self.quality_on_first_success

        self.ace_streams[ace_id] += rating
        self.ace_streams[ace_id] = max(self.ace_streams[ace_id], self.min_quality)
        self.ace_streams[ace_id] = min(self.ace_streams[ace_id], self.max_quality)
        self.save_cache()


class AceScraper:
    """Scraper object."""

    def __init__(self, site_list: list[ScrapeSite], ace_quality_cache_path: Path | None) -> None:
        """Init MyCoolObject."""
        self.site_list = site_list
        self.streams: list[FoundAceStreams] = []
        self._ace_quality = AceQuality(ace_quality_cache_path)
        for site in self.site_list:
            found_ace_streams = self._scrape_streams(site)
            if found_ace_streams:
                self.streams.append(found_ace_streams)

        self.print_streams()

    def get_streams(self) -> list[dict[str, str]]:
        """Get the found streams as a list of JSON strings."""
        streams = [stream.model_dump() for stream in self.streams]

        for found_stream in streams:
            for stream in found_stream["stream_list"]:
                stream["quality"] = self._ace_quality.get_quality(stream["ace_id"])

        return streams

    def increment_quality(self, ace_id: str, rating: int) -> None:
        """Increment the quality of a stream by ace_id."""
        self._ace_quality.increment_quality(ace_id, rating)

    def print_streams(self) -> None:
        """Print the found streams."""
        if not self.streams:
            logger.warning("Scraper found no AceStreams.")
            return

        msg = "Found AceStreams:\n"
        for found_streams in self.streams:
            msg += f"Site: {found_streams.site_name}\n"
            for stream in found_streams.stream_list:
                msg += f"  - {stream.title} ({stream.ace_id})\n"
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
            error_short = type(e).__name__
            logger.error("Error scraping site %s, %s", site.url, error_short)  # noqa: TRY400 Naa this should be shorter
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
                if ace_stream_url in [stream.ace_id for stream in streams_candidates]:
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
                        ace_id=ace_stream_url,
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

            url_no_uri = candidate.ace_id.split("acestream://")[-1].strip()

            self._ace_quality.ensure_entry(url_no_uri)
            found_streams.append(
                FoundAceStream(
                    title=title,
                    ace_id=url_no_uri,
                )
            )

        logger.debug("Streams: \n%s", "\n".join([f"{stream.title} - {stream.ace_id}" for stream in found_streams]))

        return found_streams
