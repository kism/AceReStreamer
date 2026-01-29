from datetime import UTC, datetime
from typing import TYPE_CHECKING

from lxml import etree

from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from pydantic import HttpUrl
else:
    HttpUrl = object

logger = get_logger(__name__)

_DESIRED_MIN_PROGRAMS = 5


class EPGCandidateHandler:
    def __init__(self) -> None:
        self._candidates: dict[str, EPGCandidate] = {}

    def get_number_of_candidates(self) -> int:
        return len(self._candidates)

    def _get_candidate(self, tvg_id: str, epg_url: HttpUrl) -> EPGCandidate:
        primary_key = f"{tvg_id}|{epg_url}"
        if primary_key not in self._candidates:
            self._candidates[primary_key] = EPGCandidate(tvg_id, epg_url)
        return self._candidates[primary_key]

    def add_program(self, tvg_id: str, epg_url: HttpUrl, program: etree._Element) -> None:
        candidate = self._get_candidate(tvg_id, epg_url)
        candidate.add_program(program)

    def add_channel(self, tvg_id: str, epg_url: HttpUrl, channel: etree._Element) -> None:
        candidate = self._get_candidate(tvg_id, epg_url)
        candidate.add_channel(channel)

    def get_best_candidate(self, tvg_id: str) -> EPGCandidate | None:
        # Placeholder for logic to determine the best candidate
        tvg_matches: list[EPGCandidate] = [
            candidate for candidate in self._candidates.values() if candidate.tvg_id == tvg_id
        ]
        if len(tvg_matches) == 0:
            return None
        if len(tvg_matches) == 1:
            return tvg_matches[0]

        best_candidate = tvg_matches[0]
        msg = f"Multiple EPG candidates found for tvg_id={tvg_id} >>>\n"
        for candidate in tvg_matches:
            current_candidate_score = candidate.get_epg_score()
            msg += f"  Candidate: epg_url={candidate.epg_url} score={current_candidate_score}\n"
            best_candidate_score = best_candidate.get_epg_score()
            logger.trace(
                "tvg_id=%s candidate_score=%d best_score=%d", tvg_id, current_candidate_score, best_candidate_score
            )

            if current_candidate_score > best_candidate_score:
                best_candidate = candidate

        logger.trace(msg.strip())
        return best_candidate


class EPGCandidate:
    """Model for EPG candidate channel."""

    def __init__(self, tvg_id: str, epg_url: HttpUrl) -> None:
        self.tvg_id = tvg_id
        self.epg_url = epg_url
        self._programs_bytes: list[bytes] = []
        self._channels_bytes: list[bytes] = []
        self._score: int | None = None  # Cache

    def add_program(self, program: etree._Element) -> None:
        """Add a program to the candidate."""
        # Serialize to bytes immediately to reduce memory
        self._programs_bytes.append(etree.tostring(program))
        self._score = None

    def add_channel(self, channel: etree._Element) -> None:
        """Add a channel to the candidate."""
        # Serialize to bytes immediately to reduce memory
        self._channels_bytes.append(etree.tostring(channel))
        self._score = None

    def get_channels_programs(self) -> list[etree._Element]:
        """Get all channels and programs for the candidate."""
        # Deserialize only when needed
        channels = [etree.fromstring(b) for b in self._channels_bytes]
        programs = [etree.fromstring(b) for b in self._programs_bytes]
        return channels + programs

    def get_epg_score(self) -> int:
        """Get the EPG score for the candidate."""
        if self._score is not None:
            return self._score

        n_programs_after_now = 0
        n_programs_with_description = 0
        description_total_length = 0
        n_programs_with_images = 0
        current_time = datetime.now(tz=UTC)

        # Deserialize programs only for scoring
        for program_bytes in self._programs_bytes:
            program = etree.fromstring(program_bytes)
            start_time_str = program.get("start")
            if start_time_str:
                try:
                    start_time = datetime.strptime(start_time_str, "%Y%m%d%H%M%S %z")
                    if start_time >= current_time:
                        n_programs_after_now += 1
                except ValueError:
                    logger.warning("Failed to parse start time: %s", start_time_str)
                    continue

            description_elem = program.find("desc")
            if description_elem is not None and description_elem.text and description_elem.text.strip():
                n_programs_with_description += 1
                description_total_length += len(description_elem.text.strip())

            has_image = program.find("icon") is not None
            if has_image:
                n_programs_with_images += 1

        if n_programs_after_now < _DESIRED_MIN_PROGRAMS:
            # Don't like having less than desired upcoming programs
            score = n_programs_after_now
        elif n_programs_with_description < _DESIRED_MIN_PROGRAMS:
            # Don't like having less than desired programs with descriptions.
            score = _DESIRED_MIN_PROGRAMS + n_programs_with_description
        else:
            score = (
                n_programs_after_now
                + n_programs_with_description
                + (description_total_length // 100)
                + n_programs_with_images
            )

        self._score = score
        return score
