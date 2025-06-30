"""AceQuality, for tracking quality of Ace URIs."""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from pydantic import BaseModel

from acerestreamer.utils.constants import OUR_TIMEZONE
from acerestreamer.utils.helpers import check_valid_ace_id
from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)

RE_EXTRACT_EXTINF_SECONDS = re.compile(r"EXTINF:(\d+(\.\d+)?),")
RE_EXTRACT_TS_NUMBER = re.compile(r"(\d+)\.ts$")

DEFAULT_NEXT_SEGMENT_EXPECTED = timedelta(seconds=30)
QUALITY_ON_FIRST_SUCCESS = 20
MIN_QUALITY = 0
MAX_QUALITY = 99


# region: Quality
class Quality(BaseModel):
    """Model for tracking quality of a stream."""

    quality: int = -1
    _last_segment_number: int = 0
    has_ever_worked: bool = False
    _last_segment_fetched: datetime = datetime.now(tz=OUR_TIMEZONE)
    _next_segment_expected: timedelta = DEFAULT_NEXT_SEGMENT_EXPECTED

    def update_quality(self, m3u_playlist: str) -> None:
        """Update the quality based on the m3u playlist."""
        if not m3u_playlist:  # If we don't have a playlist, it sure isn't working
            rating = -5
        else:  # We have a playlist, let's see if the new segment showed up in time
            # Get the sequence number in the hls stream m3u
            last_line = m3u_playlist.splitlines()[-1]
            ts_number_result = RE_EXTRACT_TS_NUMBER.search(last_line)
            ts_number = ts_number_result.group(1) if ts_number_result else None
            if not isinstance(ts_number, str):
                logger.warning("Could not extract TS number from last line: %s", last_line)
                return  # Weird
            ts_number_int: int = int(ts_number)

            current_time = datetime.now(tz=OUR_TIMEZONE)

            # If the stream has progressed, give it a positive rating, we can't check if it was late.
            if ts_number_int != self._last_segment_number:
                # If we get two segments it will be +2 etc, if it jumps by more than 5 I wouldn't call it healthy
                rating = min(max(ts_number_int - self._last_segment_number, 1), 5)
                self._last_segment_fetched = current_time
            elif (  # If more time has passed than expected
                # This is a fair comparison since we don't actually know when the pending segment became available
                current_time - self._last_segment_fetched > self._next_segment_expected
            ):
                rating = -5
            else:
                rating = 0

            # We are done figuring out the rating, now we update the quality
            self._last_segment_number = ts_number_int

            second_last_line = m3u_playlist.splitlines()[-2]
            seconds = RE_EXTRACT_EXTINF_SECONDS.search(second_last_line)

            if seconds:
                seconds_int = float(seconds.group(1))
                self._next_segment_expected = timedelta(seconds=seconds_int)

        if rating > 0 and not self.has_ever_worked:
            # Only need max if someone edited the json, I might do something with it later
            rating = max(QUALITY_ON_FIRST_SUCCESS, self.quality)
            self.has_ever_worked = True

        self.quality += rating
        self.quality = max(self.quality, MIN_QUALITY)
        self.quality = min(self.quality, MAX_QUALITY)


class AceQuality:
    """For tracking quality of Streams."""

    default_quality: int = -1  # Unknown quality
    currently_checking_quality = False

    def __init__(self) -> None:
        """Init AceQuality."""
        self.cache_file: Path | None = None
        self.ace_streams: dict[str, Quality] = {}
        self.external_url: str = ""

    def load_config(self, instance_path: Path, external_url: str) -> None:
        """Init AceQuality."""
        self.cache_file = instance_path / "ace_quality_cache.json"
        self.external_url = external_url
        self._load_cache()
        self._clean_cache()

    def _clean_cache(self) -> None:
        """Ensure that the cache only contains valid Ace IDs."""
        logger.debug("Cleaning AceQuality cache")
        if not self.ace_streams:
            return

        cleaned_cache = {}
        for ace_id, quality in self.ace_streams.items():
            if check_valid_ace_id(ace_id):
                cleaned_cache[ace_id] = quality
            else:
                logger.warning("Invalid Ace ID found in cache: %s", ace_id)

        self.ace_streams = cleaned_cache

    def _load_cache(self) -> None:
        if self.cache_file and self.cache_file.exists():
            try:
                with self.cache_file.open("r") as f:
                    cache_json_raw = f.read()

                ace_streams_dict = json.loads(cache_json_raw)
            except (json.JSONDecodeError, OSError):
                logger.exception("Error loading cache file: %s", self.cache_file)
                return

            for ace_id, quality_data in ace_streams_dict.items():
                try:
                    self.ace_streams[ace_id] = Quality(**quality_data)
                except TypeError:
                    error_short = type(quality_data).__name__
                    msg = (
                        f"{error_short} loading quality cache, invalid quality data for Ace ID {ace_id}: {quality_data}"
                    )
                    logger.error(msg)  # noqa: TRY400 Short error is fine
                    continue

    def save_cache(self) -> None:
        """Save the current quality cache to a file."""
        if not self.cache_file:
            return

        cache_as_dict = {ace_id: quality.model_dump() for ace_id, quality in self.ace_streams.items()}

        try:
            with self.cache_file.open("w") as f:
                json.dump(cache_as_dict, f, indent=4)
        except OSError:
            logger.exception("Error saving cache file: %s", self.cache_file)

    def get_quality(self, ace_id: str) -> Quality:
        """Get the quality of a stream by ace_id."""
        if not check_valid_ace_id(ace_id):
            return Quality()

        if ace_id not in self.ace_streams:
            self._ensure_entry(ace_id)
        return self.ace_streams[ace_id]

    def _ensure_entry(self, ace_id: str) -> None:
        """Creates an entry with defaults if it doen't exist."""
        if ace_id not in self.ace_streams:
            self.ace_streams[ace_id] = Quality()

    def increment_quality(self, ace_id: str, m3u_playlist: str) -> None:
        """Increment the quality of a stream by ace_id."""
        if not check_valid_ace_id(ace_id):
            return

        if ace_id not in self.ace_streams:
            self.ace_streams[ace_id] = Quality()

        self.ace_streams[ace_id].update_quality(m3u_playlist)

        logger.debug("Updated quality for Ace ID %s: %s", ace_id, self.ace_streams[ace_id].quality)

        self.save_cache()

    def check_missing_quality(self) -> None:
        """Cycle through all Ace IDs that have never worked and check them."""
        if self.currently_checking_quality:
            return
