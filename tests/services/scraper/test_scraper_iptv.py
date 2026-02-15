from typing import TYPE_CHECKING, Any

from pydantic import HttpUrl

from acere.core.config.scraper import ScrapeSiteIPTV
from acere.instances.paths import setup_app_path_handler
from acere.services.scraper.iptv import IPTVStreamScraper, tvg_logo
from tests.test_utils.aiohttp import FakeResponseDef, FakeSession

from . import SCRAPER_TEST_SITES
from .utils import common_title_check

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
else:
    Path = object
    pytest = object


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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _get_site_content method with aiohttp mocks."""
    # Create scraper without mocking _get_site_content
    scraper = IPTVStreamScraper()

    # Read test data
    test_content = (SCRAPER_TEST_SITES / "playlist1.m3u8").read_text(encoding="utf-8")

    # Create a mock aiohttp session that returns our test content
    fake_responses: dict[str, FakeResponseDef] = {
        "http://ace.pytest.internal/test.m3u8": {
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
        url=HttpUrl("http://ace.pytest.internal/test.m3u8"),
    )

    result = await scraper._get_site_content(site_config)
    assert result == test_content

    # Test with 404 error
    site_config_404 = ScrapeSiteIPTV(
        type="iptv",
        name="Not Found Site",
        url=HttpUrl("http://ace.pytest.internal/nonexistent.m3u8"),
    )

    result_404 = await scraper._get_site_content(site_config_404)
    assert result_404 is None


async def test_download_tvg_logo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test _download_tvg_logo method with aiohttp mocks."""
    setup_app_path_handler(instance_path=tmp_path)

    # Create fake logo content
    fake_logo_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"

    # Create mock aiohttp session
    fake_responses: dict[str, FakeResponseDef] = {
        "http://ace.pytest.internal/logos/test.png": {
            "status": 200,
            "data": fake_logo_data,
        },
        "http://ace.pytest.internal/logos/error.png": {
            "status": 404,
            "data": b"",
        },
    }

    def fake_client_session(*args: Any, **kwargs: Any) -> FakeSession:
        return FakeSession(fake_responses)

    monkeypatch.setattr("aiohttp.ClientSession", fake_client_session)

    # Test successful download
    logo_url = HttpUrl("http://ace.pytest.internal/logos/test.png")
    title = "Test Stream"

    await tvg_logo.download_and_save_logo(logo_url, title)

    # Check that the file was created
    logo_path = tmp_path / "tvg_logos" / "test-stream.png"
    assert logo_path.exists()
    assert logo_path.read_bytes() == fake_logo_data

    # Test that it doesn't re-download if file exists
    # Modify the file content to ensure it doesn't get overwritten
    modified_content = b"modified"
    logo_path.write_bytes(modified_content)

    await tvg_logo.download_and_save_logo(logo_url, title)

    # File should still have modified content (wasn't re-downloaded)
    assert logo_path.read_bytes() == modified_content

    # Test with no TVG logo URL in line
    title_no_logo = "No Logo Stream"

    await tvg_logo.download_and_save_logo(None, title_no_logo)

    # Check that no file was created
    logo_path_no_logo = tmp_path / "tvg_logos" / "no-logo-stream.png"
    assert not logo_path_no_logo.exists()

    # Test with download error (404)
    logo_url_error = HttpUrl("http://ace.pytest.internal/logos/error.png")
    title_error = "Error Stream"

    await tvg_logo.download_and_save_logo(logo_url_error, title_error)

    # Check that no file was created due to error
    logo_path_error = tmp_path / "tvg_logos" / "error-stream.png"
    assert not logo_path_error.exists()

    # Test with unsupported file extension
    logo_url_unsupported = HttpUrl("http://ace.pytest.internal/logos/test.gif")
    title_unsupported = "Unsupported Stream"

    await tvg_logo.download_and_save_logo(logo_url_unsupported, title_unsupported)

    # Check that no file was created due to unsupported extension
    logo_path_unsupported = tmp_path / "tvg_logos" / "unsupported-stream.gif"
    assert not logo_path_unsupported.exists()
