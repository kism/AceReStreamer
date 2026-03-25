"""AceStream pool entry module."""

import asyncio
from contextlib import suppress

import aiohttp
from pydantic import HttpUrl, ValidationError

from acere.services.pool.entry import BasePoolEntry
from acere.utils.ace import get_middleware_url
from acere.utils.exception_handling import log_aiohttp_exception
from acere.utils.helpers import check_valid_content_id_or_infohash
from acere.utils.hls import get_last_m3u8_segment_url
from acere.utils.logger import get_logger

from .constants import ACESTREAM_API_TIMEOUT
from .models import AceMiddlewareResponse, AceMiddlewareResponseFull, AcePoolStat

logger = get_logger(__name__)


class AcePoolEntry(BasePoolEntry):
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

        super().__init__(key=content_id)

        self._keep_alive_run_once = False

        self.ace_pid = ace_pid
        self.infohash = infohash
        self.ace_address = ace_address

        self.ace_middleware_url = get_middleware_url(
            ace_url=self.ace_address,
            content_id=self.content_id,
            ace_pid=self.ace_pid,
            transcode_audio=transcode_audio,
        )

        self._middleware_info: AceMiddlewareResponse | None = None

    @property
    def content_id(self) -> str:
        """Content ID (alias for key)."""
        return self.key

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

    def check_if_stale(self) -> bool:
        """Check if the instance is stale, with Ace-specific logging."""
        stale = super().check_if_stale()

        if stale:
            logger.debug(
                "ace_pid %d with content_id %s is stale",
                self.ace_pid,
                self.content_id,
            )

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
            with suppress(aiohttp.ClientError, asyncio.TimeoutError):
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
        except (aiohttp.ClientError, TimeoutError) as e:
            log_aiohttp_exception(logger, url, e, "Failed to stop AceStream instance")
