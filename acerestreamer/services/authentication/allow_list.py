"""Allow List Object for Authentication."""

import json
from pathlib import Path

from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)


class AllowList:
    """A simple allow list for IP addresses."""

    def __init__(self) -> None:
        """Initialize the allow list with a path to the allow list file."""
        self.allowlist_path: Path | None = None

        self.allowlist_ips: list[str] = []
        self.password: str = ""

    def load_config(self, instance_path: Path | str, password: str) -> None:
        """Load the allow list from a file."""
        self.allowlist_ips = []
        self.password = password

        if isinstance(instance_path, str):
            instance_path = Path(instance_path)

        self.allowlist_path = instance_path / "allowed_ips.json"

        self._ensure_correct_ips()

        if self.allowlist_path.exists():
            with self.allowlist_path.open("r") as f:
                try:
                    self.allowlist_ips = json.load(f)
                except json.JSONDecodeError:
                    logger.error("Failed to decode JSON from allow list file, resetting")  # noqa: TRY400 Short error for requests

        self.save()

    def _ensure_correct_ips(self) -> None:
        """Fix any incorrect IP addresses in the allow list."""
        for ip in self.allowlist_ips:
            if ip.startswith("::ffff:"):
                ip_no_prefix = ip[7:]  # Remove IPv6 prefix
                if ip_no_prefix not in self.allowlist_ips:
                    self.allowlist_ips.append(ip_no_prefix)

    def add(self, ip: str) -> None:
        """Add an IP address to the allow list."""
        if ip == "":
            logger.error("Attempted to add an empty IP address to the allow list.")
            return

        # These two being done here are to make pytest a bit easier
        if "127.0.0.1" not in self.allowlist_ips:
            self.allowlist_ips.append("127.0.0.1")

        if "::1" not in self.allowlist_ips:
            self.allowlist_ips.append("::1")

        if ip not in self.allowlist_ips:
            self.allowlist_ips.append(ip)

            if ip.startswith("::ffff:"):
                self.allowlist_ips.append(ip[7:])  # Remove IPv6 prefix

            logger.info("Added IP address to allow list: %s", ip)
            self.save()

    def check(self, ip: str) -> bool:
        """Check if an IP address is in the allow list."""
        if not self.password:
            return True
        return ip in self.allowlist_ips

    def save(self) -> None:
        """Save the allow list to a file."""
        if self.allowlist_path is not None:
            with self.allowlist_path.open("w") as f:
                json.dump(self.allowlist_ips, f)
