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
DEFAULT_DATE = datetime(1970, 1, 1, tzinfo=OUR_TIMEZONE)


# region AcePoolEntry
class AcePoolEntry(BaseModel):
    """Model for an AceStream pool entry."""

    ace_pid: int
    ace_id: str
    ace_content_path: str = ""
    ace_address: str
    healthy: bool = False
    date_started: datetime = DEFAULT_DATE
    last_used: datetime = DEFAULT_DATE
    keep_alive_active: bool = False
    ace_hls_m3u8_url: str = ""

    @model_validator(mode="after")
    def generate_hls_m3u8_url(self) -> Self:
        """Generate the HLS M3U8 URL for the AceStream instance."""
        if not self.ace_address.endswith("/"):
            self.ace_address += "/"
        self.ace_hls_m3u8_url = f"{self.ace_address}ace/manifest.m3u8?content_id={self.ace_id}&pid={self.ace_pid}"

        self.check_ace_running() # Weird place but I need to figure out __init__ with pydantic

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
        # We have locked in at one point
        condition_one = self.check_running_long_enough_to_lock_in()
        # We are not locked in
        condition_two = not self.check_locked_in()
        # We have gone past the required time to unlock
        condition_three = self.get_time_until_unlock() < timedelta(seconds=1)

        if condition_one and condition_two and condition_three:
            logger.info("Resetting keep alive for %s with ace_id %s", self.ace_address, self.ace_id)
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
                    logger.debug("Not keeping alive %s, not locked in", self.ace_address)

                if not self.keep_alive_active:  # Hopefully unreachable
                    logger.warning("Stopping keep alive thread for %s with ace_id %s", self.ace_address, self.ace_id)
                    logger.warning("This should not happen")
                    return

        if not self.keep_alive_active:
            self.keep_alive_active = True
            threading.Thread(target=keep_alive, daemon=True).start()
            logger.debug("Started keep alive thread for %s", self.ace_address)


class AcePoolEntryForAPI(AcePoolEntry):
    """Nice model with some calculated fields for the API."""

    locked_in: bool = False
    time_until_unlock: timedelta = timedelta(seconds=0)
    time_running: timedelta = timedelta(seconds=0)

    @field_serializer("time_until_unlock")
    def serialize_time_until_unlock(self, time_until_unlock: timedelta) -> int:
        """Serialize the time until unlock as a timestamp."""
        return time_until_unlock.seconds

    @field_serializer("time_running")
    def serialize_time_running(self, time_running: timedelta) -> int:
        """Serialize the time running as a timestamp."""
        return time_running.seconds


# region AcePool
class AcePool:
    """A pool of AceStream instances to distribute requests across."""

    def __init__(self, ace_address: str = "", max_size: int = 4) -> None:
        """Initialize the AcePool."""
        self.ace_address = ace_address
        self.ace_instances: list[AcePoolEntry] = []
        self.max_size = max_size
        self.ace_poolboy()

    def get_available_instance_number(self) -> int | None:
        """Get the next available AceStream instance URL."""
        if len(self.ace_instances) == self.max_size:
            logger.warning("AceStream pool is full, no available instance found.")
            return None

        instance_numbers = [instance.ace_pid for instance in self.ace_instances]

        for n in range(1, self.max_size + 1):
            if n not in instance_numbers:
                return n

        logger.warning("Something weird happened, no available instance number found.")
        return None

    def get_instance(self, ace_id: str) -> str | None:
        """Find the AceStream instance URL for a given ace_id."""
        for instance in self.ace_instances:
            if instance.ace_id == ace_id:
                instance.check_locked_in()  # Just to update the status, should be removed later
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



        self.ace_instances.append(new_instance)

        return new_instance.ace_hls_m3u8_url

    def set_content_path(self, ace_id: str, content_path: str) -> None:
        """Set the content path for a specific AceStream instance."""
        content_path_set = False
        for instance in self.ace_instances:
            if instance.ace_id == ace_id:
                if not content_path_set:
                    instance.update_last_used()
                    if instance.ace_content_path == "":
                        logger.info("Setting content path for Ace ID %s to %s", ace_id, content_path)
                    instance.ace_content_path = content_path
                    content_path_set = True
                else:  # Race condition can set two instances to the same ace_id
                    logger.warning("Content path for Ace ID %s already set to %s", ace_id, instance.ace_content_path)
                    self.ace_instances.remove(instance)

        if content_path_set:
            return

        # If not found, assign it to the next available instance
        new_instance = self.get_available_instance_number()
        if new_instance is None:
            logger.error("Cannot set_content_path.")
            return

    def get_instance_base_url_by_content_path(self, content_path: str) -> str:
        """Get the AceStream instance HLS URL by content path."""
        for instance in self.ace_instances:
            if instance.ace_content_path == content_path:
                return instance.ace_address

        logger.warning("Ace content %s path not linked to instance", content_path)
        return ""

    def get_instances_nice(self) -> list[AcePoolEntryForAPI]:
        """Get a list of AcePoolEntryForAPI instances for the API."""
        instances = []

        for instance in self.ace_instances:
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
                    ace_content_path=instance.ace_content_path,
                    ace_address=instance.ace_address,
                    healthy=instance.healthy,
                    date_started=instance.date_started,
                    last_used=instance.last_used,
                    locked_in=locked_in,
                    time_until_unlock=time_until_unlock,
                    time_running=total_time_running,
                    keep_alive_active=instance.keep_alive_active,
                )
            )

        return instances

    def clear_instance_by_ace_id(self, ace_id: str) -> bool:
        """Clear an AceStream instance by ace_id.

        Args:
            ace_id (str): The Ace ID to clear.

        Returns:
            bool: True if an instance was cleared, False otherwise.

        """
        instance_unlocked = False

        # This is the weird case, caused by a race condition probably
        for instance in self.ace_instances:
            if instance.ace_id == ace_id and instance.ace_content_path == "":
                self.ace_instances.remove(instance)
                instance_unlocked = True

        if instance_unlocked:
            return True

        # This is probably what the user wants
        for instance in self.ace_instances:
            if instance.ace_id == ace_id and instance.check_locked_in():
                self.ace_instances.remove(instance)
                instance_unlocked = True

        if instance_unlocked:
            return True

        # Anything that is not locked in
        for instance in self.ace_instances:
            if instance.ace_id == ace_id:
                self.ace_instances.remove(instance)
                instance_unlocked = True

        return instance_unlocked

    def ace_poolboy(self) -> None:
        """Run the AcePoolboy to clean up instances."""

        def ace_poolboy_thread() -> None:
            """Thread to clean up instances."""
            logger.info("Starting AcePoolboy thread to clean up instances")
            while True:
                time.sleep(10)
                for instance in self.ace_instances:
                    if instance.check_if_stale():
                        self.ace_instances.remove(instance)

        threading.Thread(target=ace_poolboy_thread, daemon=True).start()
