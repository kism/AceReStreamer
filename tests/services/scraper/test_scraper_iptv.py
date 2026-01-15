from typing import TYPE_CHECKING, Any

import pytest
from pydantic import HttpUrl

from acere.core.config import ScrapeSiteIPTV
from acere.services.scraper.iptv import IPTVStreamScraper
from acere.services.scraper.name_processor import StreamNameProcessor

from . import SCRAPER_TEST_SITES
from .utils import common_title_check

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object


@pytest.fixture
def name_processor(tmp_path: Path) -> StreamNameProcessor:
    """Fixture providing a configured StreamNameProcessor."""
    processor = StreamNameProcessor()
    processor.load_config(
        instance_path=tmp_path,
        name_replacements={},
        content_id_infohash_name_overrides={},
        category_mapping={},
    )
    return processor


@pytest.fixture
async def scraper(
    tmp_path: Path, name_processor: StreamNameProcessor, monkeypatch: pytest.MonkeyPatch
) -> IPTVStreamScraper:
    """Fixture providing a configured IPTVStreamScraper."""
    scraper = IPTVStreamScraper()
    scraper.load_config(
        instance_path=tmp_path,
        stream_name_processor=name_processor,
    )

    async def _mock_get_site_content(site: ScrapeSiteIPTV) -> str:
        assert site.url.path is not None

        site_file = SCRAPER_TEST_SITES / site.url.path.lstrip("/")

        return site_file.read_text(encoding="utf-8")

    monkeypatch.setattr(scraper, "_get_site_content", _mock_get_site_content)

    async def _mock_download_tvg_logo(*args: Any, **kwargs: Any) -> None:
        return

    monkeypatch.setattr(scraper, "_download_tvg_logo", _mock_download_tvg_logo)

    def _mock_find_tvg_logo_image(title: str) -> str:
        return f"http://pytest.internal/logos/{title.replace(' ', '_')}.png"

    monkeypatch.setattr(scraper.name_processor, "find_tvg_logo_image", _mock_find_tvg_logo_image)

    return scraper


def _get_test_sites() -> dict[str, ScrapeSiteIPTV]:
    return {
        "playlist1.m3u8": ScrapeSiteIPTV(
            type="iptv",
            name="Test Site 1",
            url=HttpUrl("http://pytest.internal/playlist1.m3u8"),
        ),
        "playlist2.m3u8": ScrapeSiteIPTV(
            type="iptv",
            name="Test Site 2",
            url=HttpUrl("http://pytest.internal/playlist2.m3u8"),
        ),
    }


async def test_site1(scraper: IPTVStreamScraper) -> None:
    """Test scraping from site1.m3u8."""
    playlist_name = "playlist1.m3u8"
    site_config = _get_test_sites()[playlist_name]

    streams = await scraper.scrape_iptv_playlists([site_config])

    assert len(streams) == 4

    for stream in streams:
        common_title_check(stream.title)
        assert "IPTV" in stream.title
        assert stream.group_title == "General"
        assert stream.tvg_logo != ""  # Its patched, so I guess we pretend it's manually downloaded


async def test_site2(scraper: IPTVStreamScraper) -> None:
    """Test scraping from site2.html."""
    playlist_name = "playlist2.m3u8"
    site_config = _get_test_sites()[playlist_name]

    streams = await scraper.scrape_iptv_playlists([site_config])

    assert len(streams) == 2

    for stream in streams:
        common_title_check(stream.title)
        assert "Stream" in stream.tvg_id
        assert "Stream" in stream.title
        assert stream.group_title == "News"
        assert stream.tvg_logo != ""
        assert stream.tvg_logo is not None
