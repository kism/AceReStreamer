"""AceStream pool management module."""

from datetime import datetime

import requests
from pydantic import BaseModel

from .logger import get_logger

logger = get_logger(__name__)

ACESTREAM_API_TIMEOUT = 3

OUR_TIMEZONE = datetime.now().astimezone().tzinfo


class AcePoolEntry(BaseModel):
    """Model for an AceStream pool entry."""

    ace_id: str = ""
    ace_content_path: str = ""
    ace_url: str
    healthy: bool = False
    date_started: datetime = datetime(1970, 1, 1, tzinfo=OUR_TIMEZONE)
    last_used: datetime = datetime(1970, 1, 1, tzinfo=OUR_TIMEZONE)

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

class AcePool:
    """A pool of AceStream instances to distribute requests across."""

    def __init__(self, ace_addresses: list[str]) -> None:
        """Initialize the AcePool with a list of AceStream addresses."""
        self.ace_instances = [AcePoolEntry(ace_url=address) for address in ace_addresses]
        for instance in self.ace_instances:
            instance.check_ace_running()
        self.current_index = 0

    def get_available_instance(self) -> AcePoolEntry | None:
        """Get the next available AceStream instance URL."""
        if not self.ace_instances:
            return None

        # Check if the current instance is healthy
        if self.ace_instances[self.current_index].healthy:
            return self.ace_instances[self.current_index]

        instance_to_use = None

        # Iterate through the instances to find the one that was used the longest time ago
        for instance in self.ace_instances:
            if instance.healthy and (instance_to_use is None or instance.last_used < instance_to_use.last_used):
                instance_to_use = instance

        return instance_to_use if instance_to_use else None

    def get_instance(self, ace_id: str) -> str | None:
        """Find the AceStream instance URL for a given ace_id."""
        for instance in self.ace_instances:
            if instance.ace_id == ace_id:
                return instance.ace_url

        # If not found, return the next available instance in a round-robin fashion
        instance = self.ace_instances[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.ace_instances)
        return instance.ace_url

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
