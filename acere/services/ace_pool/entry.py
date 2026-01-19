"""AceStream pool management module."""

import asyncio
import contextlib
from datetime import datetime, timedelta

import aiohttp
from pydantic import HttpUrl, ValidationError

from acere.constants import OUR_TIMEZONE
from acere.utils.ace import get_middleware_url
from acere.utils.helpers import check_valid_content_id_or_infohash
from acere.utils.hls import get_last_m3u8_segment_url
from acere.utils.logger import get_logger

from .constants import ACESTREAM_API_TIMEOUT
from .models import AceMiddlewareResponse, AceMiddlewareResponseFull, AcePoolStat

logger = get_logger(__name__)

LOCK_IN_TIME: timedelta = timedelta(minutes=5)
LOCK_IN_RESET_MAX: timedelta = timedelta(minutes=15)


class AcePoolEntry:
    """Model for an AceStream pool entry."""

    # region Initialization
    def __init__(
        self,
        ace_pid: int,
        ace_address: HttpUrl,
        content_id: str,
        infohash: str = "",
        *,
        transcode_audio: bool,
    ) -> None:
        """Initialize an AceStream pool entry. Does not populate URLs, use async create() method."""
        if not check_valid_content_id_or_infohash(content_id):
            msg = f"AcePoolEntry: Invalid AceStream content_id: {content_id}"
            raise ValueError(msg)

        self._keep_alive_run_once = False

        self.ace_pid = ace_pid
        self.content_id = content_id
        self.infohash = infohash
        self.ace_address = ace_address

        self.ace_middleware_url = get_middleware_url(
            ace_url=self.ace_address,
            content_id=self.content_id,
            ace_pid=self.ace_pid,
            transcode_audio=transcode_audio,
        )

        self._middleware_info: AceMiddlewareResponse | None = None

        # Required to ensure that this actually gets the current time
        self.date_started = datetime.now(tz=OUR_TIMEZONE)
        self.date_last_used = datetime.now(tz=OUR_TIMEZONE)

    @classmethod
    async def create(
        cls,
        ace_pid: int,
        ace_address: HttpUrl,
        content_id: str,
        infohash: str = "",
        *,
        transcode_audio: bool,
    ) -> AcePoolEntry:
        """Create and initialize an AceStream pool entry asynchronously, populating URLs."""
        instance = cls(ace_pid, ace_address, content_id, infohash, transcode_audio=transcode_audio)
        await instance.populate_urls()
        return instance

    async def populate_urls(self) -> None:
        """Populate the AceStream URLs for this instance."""
        try:
            timeout = aiohttp.ClientTimeout(total=ACESTREAM_API_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.ace_middleware_url) as resp:
                    resp.raise_for_status()
                    response_json = await resp.json()
                    middleware_response = AceMiddlewareResponseFull(**response_json)
        except (aiohttp.ClientError, ValueError) as e:
            logger.warning(
                "Failed to fetch AceStream URLs for content_id %s: %s",
                self.ace_middleware_url,
                str(e),
            )
            return

        if middleware_response.error:
            logger.error(
                "Error in AceStream middleware response for content_id %s: %s",
                self.content_id,
                middleware_response.error,
            )
            return

        self._middleware_info = middleware_response.response

    def update_last_used(self) -> None:
        """Update the last used timestamp."""
        self.date_last_used = datetime.now(tz=OUR_TIMEZONE)

    # region Get
    def get_m3u8_url(self) -> HttpUrl | None:
        """Get the AceStream HLS M3U8 URL."""
        if not self._middleware_info:
            logger.warning(
                "No middleware info for content_id %s, cannot get M3U8 URL",
                self.content_id,
            )
            return None

        return self._middleware_info.playback_url

    async def get_ace_stat(self) -> AcePoolStat | None:
        """Get the AceStream statistics for this instance."""
        resp_stat_json = {}
        if not self._middleware_info:
            logger.warning(
                "No middleware info for content_id %s, cannot fetch stats",
                self.content_id,
            )
            return None

        stat_url = self._middleware_info.stat_url

        try:
            timeout = aiohttp.ClientTimeout(total=ACESTREAM_API_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(stat_url.encoded_string()) as resp_stat:
                    resp_stat.raise_for_status()
                    resp_stat_json = await resp_stat.json()
                    return AcePoolStat(**resp_stat_json)
        except aiohttp.ClientError:
            pass
        except ValidationError:
            logger.exception("Failed to parse AceStream stat for content_id %s", self.content_id)
            logger.info("Did ace stream change their API?\n%s", resp_stat_json)

        return None

    def get_required_time_until_unlock(self) -> timedelta:
        """Get the time until the instance is unlocked."""
        time_now = datetime.now(tz=OUR_TIMEZONE)
        time_since_last_watched: timedelta = time_now - self.date_last_used
        time_since_date_started: timedelta = time_now - self.date_started
        return min(LOCK_IN_RESET_MAX, (time_since_date_started - time_since_last_watched))

    def get_time_until_unlock(self) -> timedelta:
        """Get the time until the instance is unlocked."""
        return self.date_last_used + self.get_required_time_until_unlock() - datetime.now(tz=OUR_TIMEZONE)

    def check_running_long_enough_to_lock_in(self) -> bool:
        """Check if the instance has been running long enough to be locked in."""
        return datetime.now(tz=OUR_TIMEZONE) - self.date_started > LOCK_IN_TIME

    # region Check
    def _check_unused_longer_than_lock_in_reset(self) -> bool:
        """Check if the instance has been unused longer than the lock-in reset time."""
        time_now = datetime.now(tz=OUR_TIMEZONE)
        time_since_last_watched: timedelta = time_now - self.date_last_used
        return time_since_last_watched > LOCK_IN_RESET_MAX

    def check_locked_in(self) -> bool:
        """Check if the instance is locked in for a certain period."""
        # If the instance has not been used for a while, it is not locked in, maximum reset time is LOCK_IN_RESET_MAX
        time_now = datetime.now(tz=OUR_TIMEZONE)
        time_since_last_watched: timedelta = time_now - self.date_last_used
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
        condition_four = self._check_unused_longer_than_lock_in_reset()

        if condition_one and condition_two and condition_three:
            logger.debug(
                "Old ace_pid %d with content_id %s is stale. one=%s, two=%s, three=%s",
                self.ace_pid,
                self.content_id,
                condition_one,
                condition_two,
                condition_three,
            )
            stale = True

        if not condition_one and condition_four:
            logger.debug(
                "New-ish and unused ace_pid %d with content_id %s is stale. one=%s, four=%s",
                self.ace_pid,
                self.content_id,
                condition_one,
                condition_four,
            )
            stale = True

        return stale

    # region Health
    async def keep_alive(self) -> None:
        """The keep_alive method, should be called by poolboy thread."""
        # If we are locked in, we keep the stream alive
        # Also check if the content_id is valid, as a failsafe
        await self.populate_urls()

        if not self._middleware_info:
            logger.warning(
                "No middleware info for content_id %s, cannot keep alive",
                self.content_id,
            )
            return

        if (
            not self.check_if_stale()
            and check_valid_content_id_or_infohash(self.content_id)
            and self._middleware_info.playback_url
        ):
            # Keep Alive
            last_segment_url = None
            with contextlib.suppress(aiohttp.ClientError, asyncio.TimeoutError):
                if not self._keep_alive_run_once and self._middleware_info.playback_url != "":
                    logger.info(
                        "Keeping alive ace_pid %d with content_id %s",
                        self.ace_pid,
                        self.content_id,
                    )
                    self._keep_alive_run_once = True
                timeout = aiohttp.ClientTimeout(total=ACESTREAM_API_TIMEOUT)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(self._middleware_info.playback_url.encoded_string()) as resp:
                        logger.trace("Keep alive, response: %s", resp.status)
                        # We need to fetch this to keep the stream kicking, maybe this can be configure in ace stream?
                        last_segment_url = get_last_m3u8_segment_url(await resp.text())

                    if last_segment_url:
                        async with session.get(last_segment_url) as resp_segment:
                            logger.trace("Keep alive ts segment, response: %s", resp_segment.status)

        else:
            logger.trace("Not keeping alive %s, not locked in", self.ace_address)

    # region Control
    async def stop(self) -> None:
        """Stop the AceStream instance, only access this externally via remove_instance_by_content_id."""
        if not self._middleware_info:
            logger.warning(
                "No middleware info for content_id %s, cannot stop instance",
                self.content_id,
            )
            return

        if not self._middleware_info.command_url:
            logger.warning(
                "No command URL for content_id %s, cannot stop instance",
                self.content_id,
            )
            return

        url = f"{self._middleware_info.command_url}?method=stop"

        try:
            timeout = aiohttp.ClientTimeout(total=ACESTREAM_API_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    logger.info("Stopped AceStream instance with content_id %s", self.content_id)
        except aiohttp.ClientError as e:
            error_short = type(e).__name__
            logger.error(
                "%s Failed to stop AceStream instance with content_id %s: ",
                error_short,
                self.content_id,
            )
