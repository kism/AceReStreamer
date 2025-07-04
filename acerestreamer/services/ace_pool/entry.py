"""AceStream pool management module."""

import contextlib
from datetime import datetime, timedelta

import requests

from acerestreamer.utils import check_valid_ace_id
from acerestreamer.utils.constants import OUR_TIMEZONE
from acerestreamer.utils.logger import get_logger

from .constants import ACESTREAM_API_TIMEOUT

logger = get_logger(__name__)

LOCK_IN_TIME: timedelta = timedelta(minutes=5)
LOCK_IN_RESET_MAX: timedelta = timedelta(minutes=15)


class AcePoolEntry:
    """Model for an AceStream pool entry."""

    def __init__(self, ace_pid: int, ace_address: str, ace_id: str, *, transcode_audio: bool) -> None:
        """Initialize an AceStream pool entry."""
        self._keep_alive_run_once = False
        self.ace_pid = ace_pid
        self.ace_id = ace_id
        self.ace_address = ace_address

        if not self.ace_address.endswith("/"):
            self.ace_address += "/"
        self.ace_hls_m3u8_url = (
            f"{self.ace_address}ace/manifest.m3u8?content_id={self.ace_id}"
            f"&transcode_ac3={str(transcode_audio).lower()}"
            f"&pid={self.ace_pid}"
        )

        # Required to ensure that this actually gets the current time
        self.date_started = datetime.now(tz=OUR_TIMEZONE)
        self.last_used = datetime.now(tz=OUR_TIMEZONE)

    def update_last_used(self) -> None:
        """Update the last used timestamp."""
        self.last_used = datetime.now(tz=OUR_TIMEZONE)

    def get_required_time_until_unlock(self) -> timedelta:
        """Get the time until the instance is unlocked."""
        time_now = datetime.now(tz=OUR_TIMEZONE)
        time_since_last_watched: timedelta = time_now - self.last_used
        time_since_date_started: timedelta = time_now - self.date_started
        return min(LOCK_IN_RESET_MAX, (time_since_date_started - time_since_last_watched))

    def get_time_until_unlock(self) -> timedelta:
        """Get the time until the instance is unlocked."""
        return self.last_used + self.get_required_time_until_unlock() - datetime.now(tz=OUR_TIMEZONE)

    def check_running_long_enough_to_lock_in(self) -> bool:
        """Check if the instance has been running long enough to be locked in."""
        return datetime.now(tz=OUR_TIMEZONE) - self.date_started > LOCK_IN_TIME

    def check_unused_longer_than_lock_in_reset(self) -> bool:
        """Check if the instance has been unused longer than the lock-in reset time."""
        time_now = datetime.now(tz=OUR_TIMEZONE)
        time_since_last_watched: timedelta = time_now - self.last_used
        return time_since_last_watched > LOCK_IN_RESET_MAX

    def check_locked_in(self) -> bool:
        """Check if the instance is locked in for a certain period."""
        # If the instance has not been used for a while, it is not locked in, maximum reset time is LOCK_IN_RESET_MAX
        time_now = datetime.now(tz=OUR_TIMEZONE)
        time_since_last_watched: timedelta = time_now - self.last_used
        required_time_to_unlock = self.get_required_time_until_unlock()

        if not self.check_running_long_enough_to_lock_in():
            return False

        if time_since_last_watched <= required_time_to_unlock:  # noqa: SIM103 Clearer to read this way
            return True

        return False  # This is the same as self.get_time_until_unlock() < timedelta(seconds=1)

    def check_if_stale(self) -> bool:
        """Check if the instance is stale, if so stop the keep_alive thread."""
        stale = False
        # If we have locked in at one point
        condition_one = self.check_running_long_enough_to_lock_in()
        # If we are not locked in
        condition_two = not self.check_locked_in()
        # If we have gone past the required time to unlock
        condition_three = self.get_time_until_unlock() < timedelta(seconds=1)
        # If it has been unused longer than the lock-in reset time
        condition_four = self.check_unused_longer_than_lock_in_reset()

        if condition_one and condition_two and condition_three:
            logger.debug(
                "Old ace_pid %d with ace_id %s is stale. one=%s, two=%s, three=%s",
                self.ace_pid,
                self.ace_id,
                condition_one,
                condition_two,
                condition_three,
            )
            stale = True

        if not condition_one and condition_four:
            logger.debug(
                "New-ish and unused ace_pid %d with ace_id %s is stale. one=%s, four=%s",
                self.ace_pid,
                self.ace_id,
                condition_one,
                condition_four,
            )
            stale = True

        return stale

    def keep_alive(self) -> None:
        """The keep_alive method, should be called by poolboy thread."""
        # If we are locked in, we keep the stream alive
        # Also check if the ace_id is valid, as a failsafe

        if self.check_locked_in() and check_valid_ace_id(self.ace_id):
            with contextlib.suppress(requests.RequestException):
                if not self._keep_alive_run_once:
                    logger.info("Keeping alive ace_pid %d with ace_id %s", self.ace_pid, self.ace_id)
                    self._keep_alive_run_once = True
                resp = requests.get(self.ace_hls_m3u8_url, timeout=ACESTREAM_API_TIMEOUT)
                logger.trace("Keep alive, response: %s", resp.status_code)

        else:
            logger.trace("Not keeping alive %s, not locked in", self.ace_address)
