"""Scraper common object."""

from typing import TYPE_CHECKING

from .cache import ScraperCache

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object


class ScraperCommon:
    """Common setupmethods for scrapers."""

    def __init__(self) -> None:
        """Initialize the ScraperCommon with a scraper cache."""
        self.scraper_cache: ScraperCache = ScraperCache()
