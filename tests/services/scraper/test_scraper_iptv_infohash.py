from typing import TYPE_CHECKING

from pydantic import HttpUrl

from acere.core.config.scraper import ScrapeSiteIPTV
from acere.services.scraper.iptv import IPTVStreamScraper

from .utils import common_title_check

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
else:
    Path = object
    pytest = object


def _get_test_sites() -> dict[str, ScrapeSiteIPTV]:
    return {
        "playlist_infohash_1.m3u8": ScrapeSiteIPTV(
            type="iptv",
            name="Test Site 1",
            url=HttpUrl("http://pytest.internal/playlist_infohash_1.m3u8"),
        ),
        "playlist_infohash_2.m3u8": ScrapeSiteIPTV(
            type="iptv",
            name="Test Site 2",
            url=HttpUrl("http://pytest.internal/playlist_infohash_2.m3u8"),
        ),
    }


async def test_site1(scraper: IPTVStreamScraper) -> None:
    """Test scraping from site1.m3u8."""
    playlist_name = "playlist_infohash_1.m3u8"
    site_config = _get_test_sites()[playlist_name]

    streams = await scraper.scrape_iptv_playlists([site_config])

    assert len(streams) == 2

    for stream in streams:
        common_title_check(stream.title)
        assert "ChannelInfo" in stream.title
        assert stream.group_title == "General"
        assert stream.tvg_logo != ""  # Its patched, so I guess we pretend it's manually downloaded
        assert stream.infohash is not None


async def test_site2(scraper: IPTVStreamScraper, caplog: pytest.LogCaptureFixture) -> None:
    """Test scraping from site2.html."""
    playlist_name = "playlist_infohash_2.m3u8"
    site_config = _get_test_sites()[playlist_name]

    with caplog.at_level("TRACE", logger="acere.services.scraper.iptv"):
        streams = await scraper.scrape_iptv_playlists([site_config])

    assert len(streams) == 2

    for stream in streams:
        common_title_check(stream.title)
        assert "ChannelInfo" in stream.tvg_id
        assert "ChannelInfo" in stream.title
        assert stream.group_title == "General"
        assert stream.tvg_logo is not None
        assert "ChannelInfo" in stream.tvg_logo
        assert stream.infohash is not None
