"""Shared fixtures for scraper tests."""

from typing import TYPE_CHECKING, Any

import pytest

from acere.core.config.scraper import ScrapeSiteIPTV
from acere.services.scraper.iptv import IPTVStreamScraper

from . import SCRAPER_TEST_SITES

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object


@pytest.fixture
async def scraper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> IPTVStreamScraper:
    """Fixture providing a configured IPTVStreamScraper."""
    scraper = IPTVStreamScraper()

    async def _mock_get_site_content(site: ScrapeSiteIPTV) -> str:
        assert site.url.path is not None

        site_file = SCRAPER_TEST_SITES / site.url.path.lstrip("/")

        return site_file.read_text(encoding="utf-8")

    monkeypatch.setattr(scraper, "_get_site_content", _mock_get_site_content)

    async def _mock_download_tvg_logo(*args: Any, **kwargs: Any) -> None:
        return

    monkeypatch.setattr("acere.services.scraper.iptv.tvg_logo.download_and_save_logo", _mock_download_tvg_logo)
    monkeypatch.setattr("acere.services.scraper.iptv.tvg_logo.fetch_logo_content", _mock_download_tvg_logo)

    def _mock_find_tvg_logo_image(title: str) -> str:
        return f"http://pytest.internal/logos/{title.replace(' ', '_')}.png"

    monkeypatch.setattr("acere.services.scraper.name_processor.find_tvg_logo_image", _mock_find_tvg_logo_image)

    return scraper
