"""AceStream pool management module."""

import threading
import time
from datetime import datetime, timedelta

import requests
from pydantic import BaseModel, ConfigDict, field_serializer

from .logger import get_logger

logger = get_logger(__name__)

ACESTREAM_API_TIMEOUT = 3

OUR_TIMEZONE = datetime.now().astimezone().tzinfo

LOCK_IN_TIME: timedelta = timedelta(minutes=3)
LOCK_IN_RESET_MAX: timedelta = timedelta(minutes=30)


class AcePoolEntry(BaseModel):
    """Model for an AceStream pool entry."""

    ace_id: str = ""
    ace_content_path: str = ""
    ace_url: str
    healthy: bool = False
    date_started: datetime = datetime(1970, 1, 1, tzinfo=OUR_TIMEZONE)
    last_used: datetime = datetime(1970, 1, 1, tzinfo=OUR_TIMEZONE)
    _keep_alive_active: bool = False

    def check_ace_running(self) -> None:
        """Use the AceStream API to check if the instance is running."""
        url = f"{self.ace_url}/webui/api/service?method=get_version"
        try:
            response = requests.get(url, timeout=ACESTREAM_API_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("Error checking AceStream instance")
            self.healthy = False

        self.healthy = True

    def update_last_used(self) -> None:
        """Update the last used timestamp."""
        self.last_used = datetime.now(tz=OUR_TIMEZONE)

    def switch_content(self, ace_id: str, content_path: str) -> None:
        """Switch the content path and ace_id for this instance."""
        self.ace_id = ace_id
        self.ace_content_path = content_path
        self.update_last_used()
        self.date_started = datetime.now(tz=OUR_TIMEZONE)
        self._keep_alive_active = False  # Reset
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
            refresh_interval = 5
            url = f"{self.ace_url}/hls/{self.ace_id}"
            while True:
                if self.check_locked_in():
                    logger.debug("Keeping alive")
                    requests.get(url, timeout=ACESTREAM_API_TIMEOUT)
                time.sleep(refresh_interval)

        if not self._keep_alive_active:
            self._keep_alive_active = True
            threading.Thread(target=keep_alive, daemon=True).start()
            logger.debug("Started keep alive thread for %s with ace_id %s", self.ace_url, self.ace_id)


class AcePoolEntryForAPI(AcePoolEntry):
    """Nice model with some calculated fields for the API."""

    model_config = ConfigDict(ser_json_timedelta="iso8601")

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
        for instance in self.ace_instances:
            if instance.ace_id == ace_id:
                instance.update_last_used()
                instance.ace_content_path = content_path
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
