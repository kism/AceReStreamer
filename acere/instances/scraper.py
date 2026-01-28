"""Scraper instance."""

from typing import TYPE_CHECKING

from acere.constants import INSTANCE_DIR
from acere.instances.config import settings

if TYPE_CHECKING:
    from acere.services.scraper import AceScraper
else:
    AceScraper = object

_ace_scraper: AceScraper | None = None


def set_ace_scraper(scraper: AceScraper) -> None:
    """Set the global AceScraper instance."""
    global _ace_scraper  # noqa: PLW0603 Lazy Loading
    _ace_scraper = scraper
    _ace_scraper.load_config(
        ace_scrape_conf=settings.scraper,
        instance_path=INSTANCE_DIR,
    )
    _ace_scraper.start_scrape_thread()


def get_ace_scraper() -> AceScraper:
    """Get the global AceScraper instance."""
    if _ace_scraper is None:
        msg = "AceScraper instance is not set."
        raise ValueError(msg)
    return _ace_scraper
