"""Cache management for the AceReStreamer scraper."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from acere.constants import SCRAPER_CACHE_DIR
from acere.utils.helpers import slugify
from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from pathlib import Path

    from pydantic import HttpUrl
else:
    HttpUrl = object
    Path = object

logger = get_logger(__name__)

DEFAULT_CACHE_MAX_AGE = timedelta(hours=2)


class ScraperCache:
    """Cache management for the AceReStreamer scraper."""

    def load_from_cache(self, url: HttpUrl) -> str:
        """Load the content from cache if available."""
        load_path = self._get_cache_file_path(url)
        if load_path.exists():
            with load_path.open("r", encoding="utf-8") as file:
                return file.read()
        return ""

    def is_cache_valid(self, url: HttpUrl, cache_max_age: timedelta = DEFAULT_CACHE_MAX_AGE) -> bool:
        """Check if the cache for the given URL is valid."""
        cache_path = self._get_cache_file_path(url)
        if cache_path.exists():
            time_now = datetime.now(tz=UTC)
            file_mod_time = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=UTC)

            time_since_mod = time_now - file_mod_time

            if time_since_mod < cache_max_age:
                logger.debug("Cache file is valid: %s [mod time %s < max age %s]", url, time_since_mod, cache_max_age)
                return True

            logger.debug("Cache file is outdated: %s [mod time %s >= max age %s]", url, time_since_mod, cache_max_age)
        else:
            logger.debug("Cache file does not exist: %s", url)

        return False

    def save_to_cache(self, url: HttpUrl, content: str) -> None:
        """Save the content to cache."""
        save_path = self._get_cache_file_path(url)
        with save_path.open("w", encoding="utf-8") as file:
            file.write(content)

    def _get_cache_file_path(self, url: HttpUrl) -> Path:
        """Get the cache file path for a given URL."""
        return SCRAPER_CACHE_DIR / f"{slugify(url.encoded_string())}.txt"
