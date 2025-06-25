"""AceStream pool management module."""

import contextlib
import threading
import time
from datetime import datetime, timedelta

import requests
from pydantic import BaseModel, field_serializer

from .config import AppConf
from .constants import OUR_TIMEZONE
from .helpers import check_valid_ace_id
from .logger import get_logger

logger = get_logger(__name__)

ACESTREAM_API_TIMEOUT = 3
LOCK_IN_TIME: timedelta = timedelta(minutes=3)
LOCK_IN_RESET_MAX: timedelta = timedelta(minutes=30)

KEEP_ALIVE_THREADS: dict[int, threading.Thread] = {}


# region AcePoolEntry
class AcePoolEntryForAPI(BaseModel):
    """Nice model with some calculated fields for the API."""

    locked_in: bool = False
    time_until_unlock: timedelta = timedelta(seconds=0)
    time_running: timedelta = timedelta(seconds=0)
    ace_pid: int
    ace_id: str
    last_used: datetime
    date_started: datetime
    ace_hls_m3u8_url: str

    @field_serializer("time_until_unlock")
    def serialize_time_until_unlock(self, time_until_unlock: timedelta) -> int:
        """Serialize the time until unlock as a timestamp."""
        return time_until_unlock.seconds

    @field_serializer("time_running")
    def serialize_time_running(self, time_running: timedelta) -> int:
        """Serialize the time running as a timestamp."""
        return time_running.seconds


class AcePoolEntry:
    """Model for an AceStream pool entry."""

    def __init__(self, ace_pid: int, ace_address: str, ace_id: str, *, transcode_audio: bool) -> None:
        """Initialize an AceStream pool entry."""
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

        self.keep_alive_active = False
        self._start_keep_alive()

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
            self.keep_alive_active = False
            stale = True

        if not condition_one and condition_four:
            logger.debug(
                "New-ish and unused ace_pid %d with ace_id %s is stale. one=%s, four=%s",
                self.ace_pid,
                self.ace_id,
                condition_one,
                condition_four,
            )
            self.keep_alive_active = False
            stale = True

        if stale and self.keep_alive_active:
            logger.info(
                "AcePoolEntry %s with pid %d is stale, removing it from the pool.",
                self.ace_id,
                self.ace_pid,
            )
            self.keep_alive_active = False  # Remember .join() the thread you are in, you will get a RuntimeError

        return stale

    def _start_keep_alive(self) -> None:
        """Ensure the AceStream stream is kept alive, Only call this once, from __init__."""

        def keep_alive() -> None:
            refresh_interval = 30

            while self.keep_alive_active:
                time.sleep(refresh_interval)

                # If we are locked in, we keep the stream alive
                # Also check if the ace_id is valid, as a failsafe
                if self.check_locked_in() and check_valid_ace_id(self.ace_id):
                    with contextlib.suppress(requests.RequestException):
                        if not self.keep_alive_active:  # Beat the race condition
                            return
                        resp = requests.get(self.ace_hls_m3u8_url, timeout=ACESTREAM_API_TIMEOUT * 2)
                        logger.trace("Keep alive, response: %s", resp.status_code)
                else:
                    logger.trace("Not keeping alive %s, not locked in", self.ace_address)

                self.check_if_stale()  # This will reset the keep_alive_active flag if the instance is stale

        if not self.keep_alive_active:
            self.keep_alive_active = True

            # Remove old keep_alive thread if it exists, never try join() yourself, so we do it before starting a new one
            if self.ace_pid in KEEP_ALIVE_THREADS:
                for _ in range(3):  # Avoid race condition, we can't join() a thread that is not alive
                    if KEEP_ALIVE_THREADS[self.ace_pid].is_alive():
                        break
                    time.sleep(1)

                if not KEEP_ALIVE_THREADS[self.ace_pid].is_alive():  # if its still not alive, weird
                    logger.warning(
                        "AcePoolEntry keep_alive, want to join() but thread not alive. "
                        "The reference will end up replaced, hopefully the thread will time out."
                    )
                    return

                KEEP_ALIVE_THREADS[self.ace_pid].join(timeout=1)
                logger.info(
                    "AcePoolEntry keep_alive, joined thread for pid: %s with ace_id: %s", self.ace_pid, self.ace_id
                )

            # Actually start the keep alive thread
            KEEP_ALIVE_THREADS[self.ace_pid] = threading.Thread(target=keep_alive, daemon=True)
            KEEP_ALIVE_THREADS[self.ace_pid].start()

            logger.info(
                "Keep alive started for pid: %s with ace_id %s, total threads: %d",
                self.ace_pid,
                self.ace_id,
                len(KEEP_ALIVE_THREADS),
            )


# region AcePool
class AcePoolForApi(BaseModel):
    """Model for the AcePool API response."""

    ace_version: str
    ace_address: str
    max_size: int
    healthy: bool
    transcode_audio: bool
    ace_instances: list[AcePoolEntryForAPI]


class AcePool:
    """A pool of AceStream instances to distribute requests across."""

    def __init__(self, app_config: AppConf | None = None) -> None:
        """Initialize the AcePool."""
        self.ace_address = app_config.ace_address if app_config else ""
        self.max_size = app_config.ace_max_streams if app_config else 0
        self.transcode_audio = app_config.transcode_audio if app_config else False
        self.ace_instances: dict[str, AcePoolEntry] = {}
        self.healthy = False
        self.ace_version = "unknown"
        self._ace_poolboy_running = False
        self.ace_poolboy()

    def load_config(self, app_config: AppConf) -> None:
        """Load the configuration for the AcePool."""
        self.ace_address = app_config.ace_address
        self.max_size = app_config.ace_max_streams
        self.transcode_audio = app_config.transcode_audio
        self.populate_ace_version()

    def populate_ace_version(self) -> None:
        """Get the AceStream version from the API."""
        version_url = f"{self.ace_address}/webui/api/service?method=get_version"
        try:
            response = requests.get(version_url, timeout=ACESTREAM_API_TIMEOUT)
            response.raise_for_status()
            version_data = response.json()

        except requests.RequestException as e:
            error_short = type(e).__name__
            logger.error("Failed to get AceStream version from %s: %s", self.ace_address, error_short)  # noqa: TRY400
            self.ace_version = "unknown"
            return

        try:
            self.ace_version = version_data["result"]["version"]
            logger.info("AceStream version %s found at %s", self.ace_version, self.ace_address)
        except KeyError:
            logger.exception("Failed to parse AceStream version from %s: %s", self.ace_address, version_data)

    def check_ace_running(self) -> bool:
        """Use the AceStream API to check if the instance is running."""
        url = f"{self.ace_address}/webui/api/service?method=get_version"
        try:
            response = requests.get(url, timeout=ACESTREAM_API_TIMEOUT)
            response.raise_for_status()
            self.healthy = True
        except requests.RequestException as e:
            error_short = type(e).__name__
            logger.error("Ace Instance %s is not healthy: %s", self.ace_address, error_short)  # noqa: TRY400 Don't need to be verbose
            self.healthy = False
        except Exception as e:  # noqa: BLE001 Last resort
            error_short = type(e).__name__
            logger.error("Ace Instance %s is not healthy for a weird reason: %s", self.ace_address, e)  # noqa: TRY400 Don't need to be verbose
            self.healthy = False

        return self.healthy

    def remove_instance_by_ace_id(self, ace_id: str) -> bool:
        """Remove an AceStream instance from the pool by ace_id."""
        if ace_id in self.ace_instances:
            logger.info("Removing AceStream instance with ace_id %s", ace_id)
            with contextlib.suppress(KeyError):
                instance_to_remove = self.ace_instances[ace_id]
                instance_to_remove.keep_alive_active = False

                del self.ace_instances[ace_id]
            return True

        return False

    def get_available_instance_number(self) -> int | None:
        """Get the next available AceStream instance URL."""
        instance_numbers = [instance.ace_pid for instance in self.ace_instances.values()]

        for n in range(1, self.max_size + 1):  # Minimum instance number is 1, per the API
            if n not in instance_numbers:
                return n

        shortlist_instances_to_reclaim = [  # We will try to reclaim a non-locked-in instance
            instance for instance in self.ace_instances.values() if not instance.check_locked_in()
        ]

        if shortlist_instances_to_reclaim:
            best_instance = min(shortlist_instances_to_reclaim, key=lambda x: x.last_used)

            logger.info("Found available AceStream instance: %s, reclaiming it.", best_instance.ace_pid)
            ace_pid = best_instance.ace_pid
            self.remove_instance_by_ace_id(best_instance.ace_id)
            return ace_pid

        logger.warning("Ace pool is full, could not get available instance.")
        return None

    def get_instance(self, ace_id: str) -> str | None:
        """Find the AceStream instance URL for a given ace_id."""
        if self.ace_instances.get(ace_id):
            instance = self.ace_instances[ace_id]
            instance.update_last_used()
            return instance.ace_hls_m3u8_url

        new_instance_number = self.get_available_instance_number()
        if new_instance_number is None:
            logger.error("No available AceStream instance number found.")
            return None

        new_instance = AcePoolEntry(
            ace_pid=new_instance_number,
            ace_id=ace_id,
            ace_address=self.ace_address,
            transcode_audio=self.transcode_audio,
        )

        self.ace_instances[ace_id] = new_instance

        return new_instance.ace_hls_m3u8_url

    def get_instances_nice(self) -> AcePoolForApi:
        """Get a list of AcePoolEntryForAPI instances for the API."""
        instances = []

        for instance in self.ace_instances.values():
            locked_in = instance.check_locked_in()
            time_until_unlock = timedelta(seconds=0)
            if locked_in:
                time_until_unlock = instance.get_time_until_unlock()

            total_time_running = timedelta(seconds=0)
            if instance.ace_id != "":
                total_time_running = datetime.now(tz=OUR_TIMEZONE) - instance.date_started

            instances.append(
                AcePoolEntryForAPI(
                    ace_pid=instance.ace_pid,
                    ace_id=instance.ace_id,
                    date_started=instance.date_started,
                    last_used=instance.last_used,
                    locked_in=locked_in,
                    time_until_unlock=time_until_unlock,
                    time_running=total_time_running,
                    ace_hls_m3u8_url=instance.ace_hls_m3u8_url,
                )
            )

        return AcePoolForApi(
            ace_address=self.ace_address,
            max_size=self.max_size,
            ace_instances=instances,
            healthy=self.healthy,
            ace_version=self.ace_version,
            transcode_audio=self.transcode_audio,
        )

    def ace_poolboy(self) -> None:
        """Run the AcePoolboy to clean up instances."""

        def ace_poolboy_thread() -> None:
            """Thread to clean up instances."""
            while True:
                self.check_ace_running()
                time.sleep(10)
                for instance in self.ace_instances.copy().values():
                    if instance.check_if_stale():
                        logger.info(
                            "ace_poolboy_thread: Resetting instance %s with ace_id %s",
                            instance.ace_pid,
                            instance.ace_id,
                        )
                        with contextlib.suppress(KeyError):
                            del self.ace_instances[instance.ace_id]

        if not self._ace_poolboy_running:
            self._ace_poolboy_running = True
            logger.info("Starting ace_poolboy_thread")
        threading.Thread(target=ace_poolboy_thread, daemon=True).start()
