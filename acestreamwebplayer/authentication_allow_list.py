"""Allow List Object for Authentication."""

import json
from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)


class AllowList:
    """A simple allow list for IP addresses."""

    def __init__(self, allowlist_path: Path | None) -> None:
        """Initialize the allow list with a path to the allow list file."""
        self.allowlist_path = allowlist_path
        self.allowlist_ips: list[str] = []
        self.load()

    def add(self, ip: str) -> None:
        """Add an IP address to the allow list."""
        if ip == "":
            logger.warning("Attempted to add an empty IP address to the allow list.")
            return

        if ip not in self.allowlist_ips:
            self.allowlist_ips.append(ip)
            logger.info("Added IP address to allow list: %s", ip)
            self.save()

    def check(self, ip: str) -> bool:
        """Check if an IP address is in the allow list."""
        return ip in self.allowlist_ips

    def load(self) -> None:
        """Load the allow list from a file."""
        if not self.allowlist_path:
            return

        if self.allowlist_path.exists():
            with self.allowlist_path.open("r") as f:
                try:
                    self.allowlist_ips = json.load(f)
                except json.JSONDecodeError:
                    logger.error("Failed to decode JSON from allow list file, resetting")  # noqa: TRY400

    def save(self) -> None:
        """Save the allow list to a file."""
        if not self.allowlist_path:
            return

        with self.allowlist_path.open("w") as f:
            json.dump(self.allowlist_ips, f)
