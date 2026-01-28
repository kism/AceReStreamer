"""Scraper common object."""

from typing import TYPE_CHECKING

from .cache import ScraperCache
from .name_processor import StreamNameProcessor

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object


class ScraperCommon:
    """Common setupmethods for scrapers."""

    def __init__(self) -> None:
        """Initialize the IPTVStreamScraper with the instance path."""
        self.scraper_cache: ScraperCache = ScraperCache()
        self.name_processor: StreamNameProcessor = StreamNameProcessor()
        self.instance_path: Path | None = None

    def load_config(
        self,
        instance_path: Path,
        stream_name_processor: StreamNameProcessor,
    ) -> None:
        """Initialize the IPTVStreamScraper with the instance path."""
        self.name_processor = stream_name_processor
        self.scraper_cache.load_config(instance_path=instance_path)
        self.instance_path = instance_path
