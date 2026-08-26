"""Scraper instance."""

from typing import TYPE_CHECKING

from acere.instances import GlobalInstance

if TYPE_CHECKING:
    from acere.services.scraper import AceScraper
else:
    AceScraper = object

_ace_scraper: GlobalInstance[AceScraper] = GlobalInstance("AceScraper")
get_ace_scraper = _ace_scraper.get


def set_ace_scraper(scraper: AceScraper) -> None:
    """Set the global AceScraper instance and start its scrape thread."""
    _ace_scraper.set(scraper)
    scraper.start_scrape_thread()
