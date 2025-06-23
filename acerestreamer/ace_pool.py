"""AceStream pool management module."""

import contextlib
import threading
import time
from datetime import datetime, timedelta
from typing import Self

import requests
from pydantic import BaseModel, field_serializer, model_validator

from .constants import OUR_TIMEZONE
from .helpers import check_valid_ace_id
from .logger import get_logger

logger = get_logger(__name__)

ACESTREAM_API_TIMEOUT = 3
LOCK_IN_TIME: timedelta = timedelta(minutes=3)
LOCK_IN_RESET_MAX: timedelta = timedelta(minutes=30)
DEFAULT_DATE_STARTED: datetime = datetime(1970, 1, 1, tzinfo=OUR_TIMEZONE)  # Default date for AceStream instances


# region AcePoolEntry
class AcePoolEntryForAPI(BaseModel):
    """Nice model with some calculated fields for the API."""

    locked_in: bool = False
    time_until_unlock: timedelta = timedelta(seconds=0)
    time_running: timedelta = timedelta(seconds=0)
    ace_pid: int
    ace_id: str
    healthy: bool
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


class AcePoolEntry(BaseModel):
    """Model for an AceStream pool entry."""

    ace_pid: int
    ace_id: str
    ace_address: str
    healthy: bool = False
    date_started: datetime = DEFAULT_DATE_STARTED
    last_used: datetime = DEFAULT_DATE_STARTED
    keep_alive_active: bool = False
    ace_hls_m3u8_url: str = ""

    @model_validator(mode="after")
    def init(self) -> Self:
        """Replacement for __init__ to get the object initialized."""
        if not self.ace_address.endswith("/"):
            self.ace_address += "/"
        self.ace_hls_m3u8_url = f"{self.ace_address}ace/manifest.m3u8?content_id={self.ace_id}&pid={self.ace_pid}"

        # Required to ensure that this actually gets the current time
        self.date_started = datetime.now(tz=OUR_TIMEZONE)
        self.last_used = datetime.now(tz=OUR_TIMEZONE)

        self.check_ace_running()  # Check if the AceStream instance is running, this updates the healthy status
        self.start_keep_alive()  # Start the keep alive thread
        return self

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
        """Check if the instance is stale and reset it if necessary."""
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
            return True

        if not condition_one and condition_four:
            logger.debug(
                "New-ish and unused ace_pid %d with ace_id %s is stale. one=%s, four=%s",
                self.ace_pid,
                self.ace_id,
                condition_one,
                condition_four,
            )
            return True

        return False

    def start_keep_alive(self) -> None:
        """Ensure the AceStream stream is kept alive."""

        def keep_alive() -> None:
            refresh_interval = 30

            while True:
                time.sleep(refresh_interval)

                if not self.ace_id:
                    logger.trace("Not keeping alive %s, no ace id set", self.ace_address)
                    continue

                if not check_valid_ace_id(self.ace_id):  # This has it's own logging warning
                    continue

                # If we are locked in, we keep the stream alive
                if self.check_locked_in():
                    with contextlib.suppress(requests.RequestException):
                        if self.check_ace_running():
                            logger.info("keep_alive %s", self.ace_hls_m3u8_url)
                            resp = requests.get(self.ace_hls_m3u8_url, timeout=ACESTREAM_API_TIMEOUT * 2)
                            logger.trace("Keep alive response: %s", resp.status_code)
                else:
                    logger.trace("Not keeping alive %s, not locked in", self.ace_address)

                if not self.keep_alive_active:  # Hopefully unreachable
                    logger.warning("Stopping keep alive thread for %s with ace_id %s", self.ace_address, self.ace_id)
                    logger.warning("This should not happen")
                    return

        if not self.keep_alive_active:
            self.keep_alive_active = True
            threading.Thread(target=keep_alive, daemon=True).start()
            logger.debug("Started keep alive thread for ace pid %s", self.ace_pid)


# region AcePool
class AcePoolForApi(BaseModel):
    """Model for the AcePool API response."""

    ace_address: str
    max_size: int
    ace_instances: list[AcePoolEntryForAPI]


class AcePool:
    """A pool of AceStream instances to distribute requests across."""

    def __init__(self, ace_address: str = "", max_size: int = 4) -> None:
        """Initialize the AcePool."""
        self.ace_address = ace_address
        self.ace_instances: dict[str, AcePoolEntry] = {}
        self.max_size = max_size
        self.ace_poolboy()

    def get_available_instance_number(self) -> int | None:
        """Get the next available AceStream instance URL."""
        instance_numbers = [instance.ace_pid for instance in self.ace_instances.values()]

        for n in range(1, self.max_size + 1):  # Minimum instance number is 1, per the API
            if n not in instance_numbers:
                return n

        for instance in self.ace_instances.values():
            if not instance.check_locked_in():
                ace_pid = instance.ace_pid
                del self.ace_instances[instance.ace_id]
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
                    healthy=instance.healthy,
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
        )

    def clear_instance_by_ace_id(self, ace_id: str) -> bool:
        """Clear an AceStream instance by ace_id.

        Args:
            ace_id (str): The Ace ID to clear.

        Returns:
            bool: True if an instance was cleared, False otherwise.

        """
        instance_unlocked = False

        if ace_id in self.ace_instances:
            del self.ace_instances[ace_id]
            instance_unlocked = True

        return instance_unlocked

    def ace_poolboy(self) -> None:
        """Run the AcePoolboy to clean up instances."""

        def ace_poolboy_thread() -> None:
            """Thread to clean up instances."""
            logger.info("Starting AcePoolboy thread to clean up instances")
            while True:
                time.sleep(10)
                for instance in self.ace_instances.values():
                    if instance.check_if_stale():
                        logger.warning(
                            "ace_poolboy_thread: Resetting instance %s with ace_id %s",
                            instance.ace_pid,
                            instance.ace_id,
                        )
                        del self.ace_instances[instance.ace_id]

        threading.Thread(target=ace_poolboy_thread, daemon=True).start()
