"""M3U Name Replacer for Ace Streamer Scraper Helper."""

from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)


class M3UNameReplacer:
    """Cache for M3U text replacements."""

    def __init__(self) -> None:
        """Initialize the cache."""
        self.cache: dict[str, str] = {}
        self.instance_path: Path | None = None

    def load_config(self, instance_path: Path | str | None = None) -> None:
        """Load the configuration for the M3U name replacer."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)

        self.instance_path = instance_path
        if instance_path:
            self._load_cache()

    def do_replacements(self, name: str) -> str:
        """Perform replacements in the M3U content."""
        if not self.instance_path:
            logger.warning("No instance path set, cannot perform M3U replacements.")
            return name

        if self.cache == {}:
            self._load_cache()

        for key, value in self.cache.items():
            if key in name:
                logger.debug("Replacing '%s' with '%s' in '%s'", key, value, name)
                name = name.replace(key, value)

        return name

    def _load_cache(self) -> None:
        """Load M3U replacements from the instance path."""
        if not self.instance_path:
            logger.warning("No instance path set, cannot perform M3U replacements.")
            return

        desired_cell_count = 2  # CSV is just my key,value pairs

        m3u_path = self.instance_path / "m3u_replacements.csv"
        if m3u_path.exists():
            with m3u_path.open("r", encoding="utf-8") as file:
                for line in file:
                    line_tmp = line.strip()
                    if not line_tmp or line_tmp.startswith("#"):
                        continue
                    parts = line_tmp.split(",")
                    if len(parts) == desired_cell_count:
                        self.cache[parts[0].strip()] = parts[1].strip()
        else:
            m3u_path.touch()
