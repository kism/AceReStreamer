"""M3U Name Replacer for Ace Streamer Scraper Helper."""

import csv
from pathlib import Path

from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)


class M3UNameReplacer:
    """Cache for M3U text replacements."""

    _CSV_DESIRED_COLUMNS: int = 2

    def __init__(self) -> None:
        """Initialize the cache."""
        self.cache: dict[str, str] = {}
        self.instance_path: Path | None = None

    def load_config(self, instance_path: Path | str) -> None:
        """Load the configuration for the M3U name replacer."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)

        self.instance_path = instance_path

        # Load the csv
        m3u_path = self.instance_path / "m3u_replacements.csv"
        if not m3u_path.exists():
            m3u_path.touch()
            return

        with m3u_path.open("r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == self._CSV_DESIRED_COLUMNS and not row[0].startswith("#"):
                    self.cache[row[0].strip()] = row[1].strip()

    def do_replacements(self, name: str) -> str:
        """Perform replacements in the M3U content."""
        for key, value in self.cache.items():
            if key in name:
                logger.debug("Replacing '%s' with '%s' in '%s'", key, value, name)
                name = name.replace(key, value)

        return name
