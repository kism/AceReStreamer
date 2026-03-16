"""Handler for content_id to xc_id mapping."""

import asyncio
import contextlib
import threading
from datetime import UTC, datetime, timedelta
from typing import ClassVar

import aiohttp
import fastapi
from pydantic import HttpUrl
from sqlmodel import select

from acere.constants import OUR_TIMEZONE
from acere.database.models import AceQualityCache
from acere.database.models.acestream import AceStreamDBEntry
from acere.instances.ace_streams import get_ace_streams_db_handler
from acere.instances.config import settings
from acere.services.ace_quality import Quality
from acere.utils.ace import ace_id_short
from acere.utils.helpers import check_valid_content_id_or_infohash
from acere.utils.logger import get_logger

from .base import BaseDatabaseHandler

_CHECK_LAST_SCRAPE_THRESHOLD = timedelta(days=1)
_CHECK_LAST_WORKED_THRESHOLD = timedelta(days=1)

_DAILY_CHECK_HOUR = 3
_DAILY_CHECK_MINUTE = 33

_async_background_tasks: set[asyncio.Task[None]] = set()
logger = get_logger(__name__)


def _seconds_until_daily_check() -> float:
    """Return seconds until the next 3:33 AM in the local timezone."""
    now = datetime.now(tz=OUR_TIMEZONE)
    target = now.replace(hour=_DAILY_CHECK_HOUR, minute=_DAILY_CHECK_MINUTE, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _has_not_worked_in_one_day(quality_cache: AceQualityCache) -> bool:
    """Return True if the stream has not had a successful quality check in the past day."""
    if quality_cache.last_quality_success_time is None:
        return True

    return datetime.now(tz=UTC) - quality_cache.last_quality_success_time >= _CHECK_LAST_WORKED_THRESHOLD


class AceQualityCacheHandler(BaseDatabaseHandler):
    """Database handler for the Ace Quality Cache."""

    _cache: ClassVar[dict[str, Quality]] = {}
    _threads: ClassVar[list[threading.Thread]] = []
    _stop_event: ClassVar[threading.Event] = threading.Event()
    _currently_checking_quality: ClassVar[bool] = False

    def get_quality(self, content_id: str) -> Quality:
        """Get the quality for a given content_id."""
        if content_id in self._cache:
            return self._cache[content_id]

        with self._get_session() as session:
            result = session.exec(select(AceQualityCache).where(AceQualityCache.content_id == content_id)).first()
            if result:
                return Quality(
                    quality=result.quality,
                    has_ever_worked=result.has_ever_worked,
                    m3u_failures=result.m3u_failures,
                )

            new_quality = Quality()
            self.set_quality(content_id=content_id, quality=new_quality)
            return new_quality

    # region SET
    def set_quality(self, content_id: str, quality: Quality) -> None:
        """Set the quality for a given content_id."""
        self._cache[content_id] = quality

        if not quality.time_to_write_to_db():
            return

        logger.trace("Writing quality cache to DB for content_id %s: %s", content_id, ace_id_short(content_id))
        with self._get_session() as session:
            result = session.exec(select(AceQualityCache).where(AceQualityCache.content_id == content_id)).first()
            if not result:
                result = AceQualityCache(content_id=content_id)
                session.add(result)

            result.quality = quality.quality
            result.m3u_failures = quality.m3u_failures

            if quality.quality_increased:
                result.last_quality_success_time = datetime.now(tz=UTC)

            session.commit()

    def increment_quality(self, content_id: str, m3u_playlist: str) -> None:
        """Increment the quality of a stream by content_id."""
        if not check_valid_content_id_or_infohash(content_id):
            return

        if "#EXT-X-STREAM-INF" in m3u_playlist:
            logger.debug(
                "Skipping quality update for Ace ID %s, multistream detected",
                content_id,
            )
            return

        entry = self.get_quality(content_id)
        entry.update_quality(m3u_playlist)

        logger.debug("Stream quality %s: %s [%s]", ace_id_short(content_id), entry.quality, entry.last_message)

        self.set_quality(content_id, entry)

    # region Quality
    async def check_missing_quality(self, attempt_delay: float = 1, stream_delay: float = 10) -> bool:
        """Check the quality of all streams.

        This is an async function since threading doesn't get app context no matter how hard I try.
        Bit of a hack.
        """
        from acere.api.routes.hls import hls  # Avoid circular import  # noqa: PLC0415

        handler = get_ace_streams_db_handler()

        if self._currently_checking_quality:
            return False

        async def check_missing_quality_thread(base_url: HttpUrl) -> None:
            try:
                AceQualityCacheHandler._currently_checking_quality = True
                await asyncio.sleep(0)  # This await means the task returns faster I think

                streams_valid_content_id = handler.get_streams()

                if not streams_valid_content_id:
                    logger.warning("No streams found to check quality.")
                    AceQualityCacheHandler._currently_checking_quality = False
                    return

                def need_to_check_quality(stream: AceStreamDBEntry) -> bool:
                    quality = self.get_quality(stream.content_id)
                    return not quality.has_ever_worked or quality.quality == 0

                ace_streams_never_worked = len(
                    [  # We also check if the quality is zero, since maybe it worked but is now dead
                        stream for stream in streams_valid_content_id if need_to_check_quality(stream)
                    ]
                )

                # We only iterate through streams from streams_valid_content_id
                # since we don't want to health check streams that are not current per the scraper.
                # Don't enumerate here, and don't bother with list comprehension tbh
                n = 0
                for stream in streams_valid_content_id:
                    if need_to_check_quality(stream):
                        n += 1
                        stream_url = f"{base_url}/{ace_id_short(stream.content_id)} {stream.title}"
                        logger.info(
                            "Checking Ace Stream %s (%d/%d)",
                            stream_url,
                            n,
                            ace_streams_never_worked,
                        )

                        for _ in range(3):
                            with contextlib.suppress(
                                aiohttp.ClientError,
                                asyncio.TimeoutError,
                                fastapi.exceptions.HTTPException,
                            ):
                                await hls(path=stream.content_id, authentication_override=True)
                            await asyncio.sleep(attempt_delay)

                        await asyncio.sleep(stream_delay)

                self.cull_stale_streams()

            except Exception as e:  # This is a background task so it won't crash the app
                exception_name = e.__class__.__name__
                logger.exception("")
                logger.error("Unhandled exception occurred during quality check: %s", exception_name)

            AceQualityCacheHandler._currently_checking_quality = False

        url = f"{settings.EXTERNAL_URL}/hls"

        task = asyncio.create_task(check_missing_quality_thread(base_url=HttpUrl(url)))
        _async_background_tasks.add(task)
        task.add_done_callback(_async_background_tasks.discard)

        return True

    # region Culling
    def cull_stale_streams(self) -> None:
        """Remove streams that have not worked or been scraped in the past day."""
        handler = get_ace_streams_db_handler()
        streams = handler.get_streams()
        now = datetime.now(tz=UTC)

        with self._get_session() as session:
            quality_entries = session.exec(select(AceQualityCache)).all()
            quality_map = {entry.content_id: entry for entry in quality_entries}

        for stream in streams:
            if now - stream.last_scraped_time >= _CHECK_LAST_SCRAPE_THRESHOLD:
                logger.info(
                    "Culling stream %s (%s): not scraped in 1 day",
                    ace_id_short(stream.content_id),
                    stream.title,
                )
                handler.delete_by_content_id(stream.content_id)
                continue

            quality_entry = quality_map.get(stream.content_id)
            if quality_entry is None or _has_not_worked_in_one_day(quality_entry):
                logger.info(
                    "Culling stream %s (%s): not worked in 1 day",
                    ace_id_short(stream.content_id),
                    stream.title,
                )
                handler.delete_by_content_id(stream.content_id)

    # region Daily Schedule
    def start_daily_check_thread(self) -> None:
        """Start a thread that triggers the quality check at 3:33 AM each day."""
        loop = asyncio.get_running_loop()

        def _run() -> None:
            while not self._stop_event.is_set():
                seconds = _seconds_until_daily_check()
                logger.info(
                    "Next scheduled quality check in %.0f seconds (at %02d:%02d local time)",
                    seconds,
                    _DAILY_CHECK_HOUR,
                    _DAILY_CHECK_MINUTE,
                )
                if self._stop_event.wait(seconds):
                    break

                logger.info("Starting daily scheduled quality check and stream culling")
                asyncio.run_coroutine_threadsafe(self.check_missing_quality(), loop)

                # Wait briefly to avoid re-triggering within the same minute
                if self._stop_event.wait(120):
                    break

        thread = threading.Thread(target=_run, name="AceQualityCache: daily_check", daemon=True)
        thread.start()
        self._threads.append(thread)

    def stop_all_threads(self) -> None:
        """Stop all threads managed by this handler."""
        if not self._threads:
            return

        logger.info("Stopping all %s threads", self.__class__.__name__)
        self._stop_event.set()
        for thread in self._threads.copy():
            if thread.is_alive():
                thread.join(timeout=60)
                if not thread.is_alive():
                    self._threads.remove(thread)
                else:
                    logger.warning("Thread %s did not stop in time.", thread.name)

        self._stop_event.clear()

    # region Helpers
    def clean_table(self) -> None:
        """Clean the quality cache table."""
        with self._get_session() as session:
            all_entries = session.exec(select(AceQualityCache)).all()
            for entry in all_entries:
                if not check_valid_content_id_or_infohash(entry.content_id):
                    logger.error(
                        "Found invalid content_id in quality cache: %s",
                        entry.content_id,
                    )
                    session.delete(entry)
            session.commit()
