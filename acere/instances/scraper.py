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
        epg_conf_list=settings.epgs,
        instance_path=INSTANCE_DIR,
        external_url=settings.EXTERNAL_URL,
        ace_url=settings.app.ace_address,
    )
    _ace_scraper.start_scrape_thread()


def get_ace_scraper() -> AceScraper:
    """Get the global AceScraper instance."""
    if _ace_scraper is None:
        msg = "AceScraper instance is not set."
        raise ValueError(msg)
    return _ace_scraper
