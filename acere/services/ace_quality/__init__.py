"""AceQuality, for tracking quality of Ace URIs."""

import re
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel

from acere.utils.logger import get_logger

logger = get_logger(__name__)

RE_EXTRACT_EXTINF_SECONDS = re.compile(r"EXTINF:(\d+(\.\d+)?),")
RE_EXTRACT_TS_NUMBER = re.compile(r"(\d+)\.ts.*$")

DEFAULT_NEXT_SEGMENT_EXPECTED = timedelta(seconds=30)
QUALITY_ON_FIRST_SUCCESS = 20
MIN_QUALITY = 0
MAX_QUALITY = 99
LATE_SEGMENT_PUNISHMENT = -4
TIME_BETWEEN_DB_WRITES = timedelta(minutes=1)

NEW_STREAM_THRESHOLD = 20  # If the TS number is below this, we are more lenient with the quality rating


# region: Quality
class Quality(BaseModel):
    """Model for tracking quality of a stream."""

    quality: int = -1
    has_ever_worked: bool = False
    m3u_failures: int = 0
    _last_segment_number: int = 0
    _last_segment_fetched: datetime = datetime.now(tz=UTC)
    _last_db_write: datetime = datetime.min.replace(tzinfo=UTC)
    _next_segment_expected: timedelta = DEFAULT_NEXT_SEGMENT_EXPECTED
    last_message: str = ""

    def update_quality(self, m3u_playlist: str) -> None:
        """Update the quality based on the m3u playlist."""
        rating = 0
        self.last_message = ""
        # If we don't have a playlist, it sure isn't working, this will always happen when starting a new stream though
        if not m3u_playlist:
            rating = max(0 - self.m3u_failures, -5)
            self.m3u_failures += 1
        else:  # We have a playlist, let's see if the new segment showed up in time
            # Get the sequence number in the hls stream m3u
            self.m3u_failures = 0  # Reset
            last_line = m3u_playlist.splitlines()[-1]
            ts_number_result = RE_EXTRACT_TS_NUMBER.search(last_line)
            ts_number = ts_number_result.group(1) if ts_number_result else None
            if not isinstance(ts_number, str):
                logger.warning("Could not extract TS number from last line: %s", last_line)
                return  # Weird
            ts_number_int: int = int(ts_number)

            current_time = datetime.now(tz=UTC)

            # Get the time between now and when we last successfully fetched a segment
            time_since_last_segment = current_time - self._last_segment_fetched

            segment_is_late = (
                time_since_last_segment > self._next_segment_expected
            )  # If more time has passed than expected

            # If the stream has progressed, give it a positive rating, we can't check if it was late.
            if ts_number_int != self._last_segment_number:
                # If we get two segments it will be +2 etc, if it jumps by more than 5 I wouldn't call it healthy
                n_new_segments = ts_number_int - self._last_segment_number
                rating = min(max(n_new_segments, 1), 5)
                self._last_segment_fetched = current_time
                self.last_message = (
                    f"Score +{rating} ({n_new_segments} new {'segments' if n_new_segments > 1 else 'segment'})"
                )
            elif segment_is_late:
                # This is a fair comparison since we don't actually know when the pending segment became available
                # If it's a new stream, we are less harsh
                rating = -1 if ts_number_int < NEW_STREAM_THRESHOLD else LATE_SEGMENT_PUNISHMENT
                time_diff = time_since_last_segment - self._next_segment_expected
                self.last_message = f"Score {rating} (Expected segment {time_diff.seconds}s ago)"
            else:
                # No segment was due at time of checking
                self.last_message = "Score +0 (no new segment due)"
                rating = 0

            # We are done figuring out the rating, now we update the quality
            self._last_segment_number = ts_number_int

            second_last_line = m3u_playlist.splitlines()[-2]
            seconds = RE_EXTRACT_EXTINF_SECONDS.search(second_last_line)

            if seconds:
                seconds_int = float(seconds.group(1))
                self._next_segment_expected = timedelta(seconds=seconds_int)

        if rating > 0:  # If it works at all, we set the quality to a minimum of QUALITY_ON_FIRST_SUCCESS
            self.quality = max(QUALITY_ON_FIRST_SUCCESS, self.quality)
            self.has_ever_worked = True

        self.quality += rating
        self.quality = max(self.quality, MIN_QUALITY)
        self.quality = min(self.quality, MAX_QUALITY)
        logger.trace("New quality %s %s", self.quality, f"(rating: {rating})")

    def time_to_write_to_db(self) -> bool:
        """Determine if it's time to write the quality to the database."""
        current_time = datetime.now(tz=UTC)
        if current_time - self._last_db_write >= TIME_BETWEEN_DB_WRITES:
            self._last_db_write = current_time
            return True

        return False
