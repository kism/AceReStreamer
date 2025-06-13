"""AceStream pool management module."""

from pydantic import BaseModel


class AcePoolEntry(BaseModel):
    """Model for an AceStream pool entry."""

    ace_id: str = ""
    ace_content_path: str = ""
    ace_url: str


class AcePool:
    """A pool of AceStream instances to distribute requests across."""

    def __init__(self, ace_addresses: list[str]) -> None:
        """Initialize the AcePool with a list of AceStream addresses."""
        self.ace_instances = [AcePoolEntry(ace_url=address) for address in ace_addresses]
        self.current_index = 0

    def get_instance(self, ace_id: str) -> str:
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
                instance.ace_content_path = content_path
                return

        # If not found, assign it to the next available instance
        instance = self.ace_instances[self.current_index]
        instance.ace_id = ace_id
        instance.ace_content_path = content_path

    def get_instance_by_content_path(self, content_path: str) -> str:
        """Get the AceStream instance URL by content path."""
        for instance in self.ace_instances:
            if instance.ace_content_path == content_path:
                return instance.ace_url

        return ""
