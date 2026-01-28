from typing import TYPE_CHECKING, Any

import pytest
from pydantic import HttpUrl

from acere.core.config import ScrapeSiteIPTV
from acere.services.scraper.iptv import IPTVStreamScraper
from acere.services.scraper.name_processor import StreamNameProcessor
from tests.test_utils.aiohttp import FakeResponseDef, FakeSession

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


async def test_get_site_content(
    tmp_path: Path,
    name_processor: StreamNameProcessor,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _get_site_content method with aiohttp mocks."""
    # Create scraper without mocking _get_site_content
    scraper = IPTVStreamScraper()
    scraper.load_config(
        instance_path=tmp_path,
        stream_name_processor=name_processor,
    )

    # Read test data
    test_content = (SCRAPER_TEST_SITES / "playlist1.m3u8").read_text(encoding="utf-8")

    # Create a mock aiohttp session that returns our test content
    fake_responses: dict[str, FakeResponseDef] = {
        "http://example.com/test.m3u8": {
            "status": 200,
            "data": test_content,
        }
    }

    # Patch aiohttp.ClientSession to return our FakeSession
    def fake_client_session(*args: Any, **kwargs: Any) -> FakeSession:
        return FakeSession(fake_responses)

    monkeypatch.setattr("aiohttp.ClientSession", fake_client_session)

    # Test successful fetch
    site_config = ScrapeSiteIPTV(
        type="iptv",
        name="Test Site",
        url=HttpUrl("http://example.com/test.m3u8"),
    )

    result = await scraper._get_site_content(site_config)
    assert result == test_content

    # Test with 404 error
    site_config_404 = ScrapeSiteIPTV(
        type="iptv",
        name="Not Found Site",
        url=HttpUrl("http://example.com/nonexistent.m3u8"),
    )

    result_404 = await scraper._get_site_content(site_config_404)
    assert result_404 is None


async def test_download_tvg_logo(
    tmp_path: Path,
    name_processor: StreamNameProcessor,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _download_tvg_logo method with aiohttp mocks."""
    scraper = IPTVStreamScraper()
    scraper.load_config(
        instance_path=tmp_path,
        stream_name_processor=name_processor,
    )

    # Create fake logo content
    fake_logo_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"

    # Create mock aiohttp session
    fake_responses: dict[str, FakeResponseDef] = {
        "http://example.com/logos/test.png": {
            "status": 200,
            "data": fake_logo_data,
        },
        "http://example.com/logos/error.png": {
            "status": 404,
            "data": b"",
        },
    }

    def fake_client_session(*args: Any, **kwargs: Any) -> FakeSession:
        return FakeSession(fake_responses)

    monkeypatch.setattr("aiohttp.ClientSession", fake_client_session)

    # Test successful download
    line = '#EXTINF:-1 tvg-logo="http://example.com/logos/test.png",Test Stream'
    title = "Test Stream"

    await scraper._download_tvg_logo(line, title)

    # Check that the file was created
    logo_path = tmp_path / "tvg_logos" / "test-stream.png"
    assert logo_path.exists()
    assert logo_path.read_bytes() == fake_logo_data

    # Test that it doesn't re-download if file exists
    # Modify the file content to ensure it doesn't get overwritten
    modified_content = b"modified"
    logo_path.write_bytes(modified_content)

    await scraper._download_tvg_logo(line, title)

    # File should still have modified content (wasn't re-downloaded)
    assert logo_path.read_bytes() == modified_content

    # Test with no TVG logo URL in line
    line_no_logo = "#EXTINF:-1,No Logo Stream"
    title_no_logo = "No Logo Stream"

    await scraper._download_tvg_logo(line_no_logo, title_no_logo)

    # Check that no file was created
    logo_path_no_logo = tmp_path / "tvg_logos" / "no-logo-stream.png"
    assert not logo_path_no_logo.exists()

    # Test with download error (404)
    line_error = '#EXTINF:-1 tvg-logo="http://example.com/logos/error.png",Error Stream'
    title_error = "Error Stream"

    await scraper._download_tvg_logo(line_error, title_error)

    # Check that no file was created due to error
    logo_path_error = tmp_path / "tvg_logos" / "error-stream.png"
    assert not logo_path_error.exists()

    # Test with unsupported file extension
    line_unsupported = '#EXTINF:-1 tvg-logo="http://example.com/logos/test.gif",Unsupported Stream'
    title_unsupported = "Unsupported Stream"

    await scraper._download_tvg_logo(line_unsupported, title_unsupported)

    # Check that no file was created due to unsupported extension
    logo_path_unsupported = tmp_path / "tvg_logos" / "unsupported-stream.gif"
    assert not logo_path_unsupported.exists()
