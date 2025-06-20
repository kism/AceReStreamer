"""Cache management for the AceReStreamer scraper."""

from datetime import datetime, timedelta
from pathlib import Path

from .constants import OUR_TIMEZONE
from .flask_helpers import get_current_app
from .helpers import slugify

current_app = get_current_app()

CACHE_MAX_AGE = timedelta(days=1)


class ScraperCache:
    """Cache management for the AceReStreamer scraper."""

    def __init__(self) -> None:
        """Initialize the ScraperCache."""
        self.cache_path = Path(current_app.instance_path) / "scraper_cache"
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def load_from_cache(self, url: str) -> str:
        """Load the content from cache if available."""
        cache_path = self.cache_path / f"{slugify(url)}.txt"
        if cache_path.exists():
            with cache_path.open("r", encoding="utf-8") as file:
                return file.read()
        return ""

    def is_cache_valid(self, url: str, cache_max_age: timedelta = CACHE_MAX_AGE) -> bool:
        """Check if the cache for the given URL is valid."""
        cache_path = self.cache_path / f"{slugify(url)}.txt"
        if cache_path.exists():
            time_now = datetime.now(tz=OUR_TIMEZONE)
            file_mod_time = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=OUR_TIMEZONE)

            if time_now - file_mod_time < cache_max_age:
                return True

        return False

    def save_to_cache(self, url: str, content: str) -> None:
        """Save the content to cache."""
        cache_path = self.cache_path / f"{slugify(url)}.txt"
        cache_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the cache directory exists
        with cache_path.open("w", encoding="utf-8") as file:
            file.write(content)
