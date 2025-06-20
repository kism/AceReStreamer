"""AceStream pool management module."""

import contextlib
import threading
import time
from datetime import datetime, timedelta

import requests
from pydantic import BaseModel, field_serializer

from .constants import OUR_TIMEZONE
from .logger import get_logger

logger = get_logger(__name__)

ACESTREAM_API_TIMEOUT = 3
LOCK_IN_TIME: timedelta = timedelta(minutes=3)
LOCK_IN_RESET_MAX: timedelta = timedelta(minutes=30)
DEFAULT_DATE = datetime(1970, 1, 1, tzinfo=OUR_TIMEZONE)


class AcePoolEntry(BaseModel):
    """Model for an AceStream pool entry."""

    ace_id: str = ""
    ace_content_path: str = ""
    ace_url: str
    healthy: bool = False
    date_started: datetime = DEFAULT_DATE
    last_used: datetime = DEFAULT_DATE
    keep_alive_active: bool = False

    def check_ace_running(self) -> bool:
        """Use the AceStream API to check if the instance is running."""
        url = f"{self.ace_url}/webui/api/service?method=get_version"
        try:
            response = requests.get(url, timeout=ACESTREAM_API_TIMEOUT)
            response.raise_for_status()
            self.healthy = True
        except requests.RequestException as e:
            error_short = type(e).__name__
            logger.error("Ace Instance %s is not healthy: %s", self.ace_url, error_short)  # noqa: TRY400 Don't need to be verbose
            self.healthy = False
        except Exception as e:  # noqa: BLE001 Last resort
            error_short = type(e).__name__
            logger.error("Ace Instance %s is not healthy for a weird reason: %s", self.ace_url, e)  # noqa: TRY400 Don't need to be verbose
            self.healthy = False

        return self.healthy

    def update_last_used(self) -> None:
        """Update the last used timestamp."""
        self.last_used = datetime.now(tz=OUR_TIMEZONE)

    def reset_content(self) -> None:
        """Reset the content path and ace_id for this instance."""
        logger.info("Resetting content for Ace ID %s on %s", self.ace_id, self.ace_url)
        self.ace_id = ""
        self.ace_content_path = ""
        self.update_last_used()
        self.date_started = DEFAULT_DATE
        self.keep_alive_active = False
        self.check_ace_running()

    def switch_content(self, ace_id: str, content_path: str) -> None:
        """Switch the content path and ace_id for this instance."""
        logger.info("Switching instance %s to ace id %s", self.ace_url, ace_id)
        self.ace_id = ace_id
        self.ace_content_path = content_path
        self.update_last_used()
        self.date_started = datetime.now(tz=OUR_TIMEZONE)
        self.keep_alive_active = False  # Reset
        self.start_keep_alive()

    def get_time_until_unlock(self) -> timedelta:
        """Get the time until the instance is unlocked."""
        time_now = datetime.now(tz=OUR_TIMEZONE)
        time_since_last_watched: timedelta = time_now - self.last_used
        time_since_date_started: timedelta = time_now - self.date_started
        return min(LOCK_IN_RESET_MAX, (time_since_date_started - time_since_last_watched))

    def check_locked_in(self) -> bool:
        """Check if the instance is locked in for a certain period."""
        if self.ace_id == "":
            return False

        # If the instance has not been used for a while, it is not locked in, maximum reset time is LOCK_IN_RESET_MAX
        time_now = datetime.now(tz=OUR_TIMEZONE)
        time_since_date_started: timedelta = time_now - self.date_started
        time_since_last_watched: timedelta = time_now - self.last_used
        required_time_to_unlock = self.get_time_until_unlock()

        if time_since_date_started < LOCK_IN_TIME:
            return False

        if time_since_last_watched <= required_time_to_unlock:  # noqa: SIM103 Clearer to read this way
            return True

        return False

    def start_keep_alive(self) -> None:
        """Ensure the AceStream stream is kept alive."""

        def keep_alive() -> None:
            refresh_interval = 30
            url = f"{self.ace_url}/ace/manifest.m3u8?content_id={self.ace_id}"
            while True:
                # If we are locked in, we keep the stream alive
                if self.check_locked_in():
                    with contextlib.suppress(requests.RequestException):
                        if self.check_ace_running():
                            resp = requests.get(url, timeout=ACESTREAM_API_TIMEOUT * 2)
                            logger.trace("Keep alive response: %s", resp.status_code)
                # If we are not locked in, we check if we have been previously locked in, and reset if needed
                elif self.date_started - datetime.now(tz=OUR_TIMEZONE) > LOCK_IN_RESET_MAX:
                    logger.debug("Resetting keep alive for %s with ace_id %s", self.ace_url, self.ace_id)
                    self.reset_content()
                    return
                time.sleep(refresh_interval)

        if not self.keep_alive_active:
            self.keep_alive_active = True
            threading.Thread(target=keep_alive, daemon=True).start()
            logger.debug("Started keep alive thread for %s with ace_id %s", self.ace_url, self.ace_id)


class AcePoolEntryForAPI(AcePoolEntry):
    """Nice model with some calculated fields for the API."""

    locked_in: bool = False
    time_until_unlock: timedelta = timedelta(seconds=0)

    @field_serializer("time_until_unlock")
    def serialize_timedelta(self, time_until_unlock: timedelta) -> int:
        """Serialize the time until unlock as a timestamp."""
        return time_until_unlock.seconds


class AcePool:
    """A pool of AceStream instances to distribute requests across."""

    def __init__(self, ace_addresses: list[str]) -> None:
        """Initialize the AcePool with a list of AceStream addresses."""
        self.ace_instances = [AcePoolEntry(ace_url=address) for address in ace_addresses]
        for instance in self.ace_instances:
            instance.check_ace_running()
            instance.check_locked_in()

    def get_available_instance(self) -> AcePoolEntry | None:
        """Get the next available AceStream instance URL."""
        if not self.ace_instances:
            return None

        instance_to_use = None

        # Iterate through the instances to find the one that was used the longest time ago
        for instance in self.ace_instances:
            if instance.check_locked_in():
                continue

            instance.check_ace_running()

            if instance.healthy and (instance_to_use is None or instance.last_used < instance_to_use.last_used):
                instance_to_use = instance

        return instance_to_use if instance_to_use else None

    def get_instance(self, ace_id: str) -> str | None:
        """Find the AceStream instance URL for a given ace_id."""
        for instance in self.ace_instances:
            if instance.ace_id == ace_id:
                instance.check_locked_in()  # Just to update the status, should be removed later
                return instance.ace_url

        # If not found, return the next available instance in a round-robin fashion
        instance_to_claim: AcePoolEntry | None = self.get_available_instance()

        if instance_to_claim is None:
            logger.error("No available AceStream instance found.")
            return None

        instance_to_claim.switch_content(ace_id, "")

        return instance_to_claim.ace_url

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
                    instance.reset_content()

        if content_path_set:
            return

        # If not found, assign it to the next available instance
        new_instance = self.get_available_instance()
        if new_instance is None:
            logger.error("No available AceStream instance to set content path.")
            return

        if new_instance is not None:
            new_instance.switch_content(ace_id, content_path)

    def get_instance_by_content_path(self, content_path: str) -> str:
        """Get the AceStream instance URL by content path."""
        for instance in self.ace_instances:
            if instance.ace_content_path == content_path:
                return instance.ace_url

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

            instances.append(
                AcePoolEntryForAPI(
                    ace_id=instance.ace_id,
                    ace_content_path=instance.ace_content_path,
                    ace_url=instance.ace_url,
                    healthy=instance.healthy,
                    date_started=instance.date_started,
                    last_used=instance.last_used,
                    locked_in=locked_in,
                    time_until_unlock=time_until_unlock,
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
                instance.reset_content()
                instance_unlocked = True

        if instance_unlocked:
            return True

        # This is probably what the user wants
        for instance in self.ace_instances:
            if instance.ace_id == ace_id and instance.check_locked_in():
                instance.reset_content()
                instance_unlocked = True

        if instance_unlocked:
            return True

        # Anything that is not locked in
        for instance in self.ace_instances:
            if instance.ace_id == ace_id:
                instance.reset_content()
                instance_unlocked = True

        return instance_unlocked
