"""Cache management for the AceReStreamer scraper."""

from datetime import datetime, timedelta
from pathlib import Path

from .constants import OUR_TIMEZONE
from .flask_helpers import get_current_app
from .helpers import slugify

current_app = get_current_app()


class ScraperCache:
    """Cache management for the AceReStreamer scraper."""

    def __init__(
        self, instance_path: Path | None = None
    ) -> None:  # This is a hack, but one day i'll restructure (lies)
        """Initialize the cache directory."""
        self._ready = False
        if instance_path is not None:
            self.cache_path = instance_path / "scraper_cache"
            self.cache_path.mkdir(parents=True, exist_ok=True)
            self._ready = True

    def load_from_cache(self, url: str) -> str:
        """Load the content from cache if available."""
        if not self._ready:
            return ""

        cache_path = self.cache_path / f"{slugify(url)}.txt"
        if cache_path.exists():
            with cache_path.open("r", encoding="utf-8") as file:
                return file.read()
        return ""

    def is_cache_valid(self, url: str, cache_max_age: timedelta = timedelta(days=1)) -> bool:
        """Check if the cache for the given URL is valid."""
        if not self._ready:
            return False

        cache_path = self.cache_path / f"{slugify(url)}.txt"
        if cache_path.exists():
            time_now = datetime.now(tz=OUR_TIMEZONE)
            file_mod_time = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=OUR_TIMEZONE)

            if time_now - file_mod_time < cache_max_age:
                return True

        return False

    def save_to_cache(self, url: str, content: str) -> None:
        """Save the content to cache."""
        if not self._ready:
            return

        cache_path = self.cache_path / f"{slugify(url)}.txt"
        cache_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the cache directory exists
        with cache_path.open("w", encoding="utf-8") as file:
            file.write(content)


scraper_cache = ScraperCache()


def start_scraper_cache(instance_path: str) -> None:
    """Initialize the scraper cache with the given instance path."""
    global scraper_cache
    scraper_cache = ScraperCache(Path(instance_path))
