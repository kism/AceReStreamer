"""Cache management for the AceReStreamer scraper."""

from datetime import datetime, timedelta
from pathlib import Path

from .constants import OUR_TIMEZONE
from .helpers import slugify


class ScraperCache:
    """Cache management for the AceReStreamer scraper."""

    def __init__(self) -> None:
        """Initialize the cache directory."""
        self.cache_path: Path | None = None

    def load_config(self, instance_path: Path | str) -> None:
        """Load the configuration for the scraper cache."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)
        self.cache_path = instance_path / "scraper_cache"
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def load_from_cache(self, url: str) -> str:
        """Load the content from cache if available."""
        load_path = self._get_cache_file_path(url)
        if load_path.exists():
            with load_path.open("r", encoding="utf-8") as file:
                return file.read()
        return ""

    def is_cache_valid(self, url: str, cache_max_age: timedelta = timedelta(days=1)) -> bool:
        """Check if the cache for the given URL is valid."""
        cache_path = self._get_cache_file_path(url)
        if cache_path.exists():
            time_now = datetime.now(tz=OUR_TIMEZONE)
            file_mod_time = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=OUR_TIMEZONE)

            if time_now - file_mod_time < cache_max_age:
                return True

        return False

    def save_to_cache(self, url: str, content: str) -> None:
        """Save the content to cache."""
        save_path = self._get_cache_file_path(url)
        with save_path.open("w", encoding="utf-8") as file:
            file.write(content)

    def _get_cache_file_path(self, url: str) -> Path:
        """Get the cache file path for a given URL."""
        if not self.cache_path:
            msg = "Cache path is not set. Call load_config() first."
            raise ValueError(msg)
        return self.cache_path / f"{slugify(url)}.txt"
