"""Scraper common object."""

from typing import TYPE_CHECKING

from acere.constants import INSTANCE_DIR, TVG_LOGOS_DIR

from .cache import ScraperCache

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object


class ScraperCommon:
    """Common setupmethods for scrapers."""

    def __init__(self, instance_path: Path | None = None) -> None:
        """Initialize the IPTVStreamScraper with the instance path."""
        self._instance_path: Path = instance_path or INSTANCE_DIR
        self._tvg_logos_path: Path = self._instance_path / TVG_LOGOS_DIR.name
        self.scraper_cache: ScraperCache = ScraperCache(instance_path=self._instance_path)
