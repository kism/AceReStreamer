"""Scraper common object."""

from pathlib import Path

from acere.database.handlers import CategoryXCCategoryIDDatabaseHandler

from .cache import ScraperCache
from .name_processor import StreamNameProcessor


class ScraperCommon:
    """Common setupmethods for scrapers."""

    def __init__(self) -> None:
        """Initialize the IPTVStreamScraper with the instance path."""
        self.scraper_cache: ScraperCache = ScraperCache()
        self.name_processor: StreamNameProcessor = StreamNameProcessor()
        self.instance_path: Path | None = None
        self.category_xc_category_id_mapping: CategoryXCCategoryIDDatabaseHandler | None = None

    def load_config(
        self,
        instance_path: Path,
        stream_name_processor: StreamNameProcessor,
        *,
        adhoc_mode: bool = False,
    ) -> None:
        """Initialize the IPTVStreamScraper with the instance path."""
        self.name_processor = stream_name_processor
        self.scraper_cache.load_config(instance_path=instance_path)
        self.instance_path = instance_path

        if not adhoc_mode:
            self.category_xc_category_id_mapping = CategoryXCCategoryIDDatabaseHandler()
