import inspect
import logging
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import HttpUrl

from acere.cli.scraper.playlist import PlaylistCreator
from acere.constants import OUR_TIMEZONE
from acere.core.config import AceReStreamerConf, ScrapeSiteIPTV
from acere.services.scraper import IPTVStreamScraper
from acere.services.scraper.name_processor import StreamNameProcessor

_M3U_TEST_DATA_DIR = Path(__file__).parent / "m3u8"


@pytest.fixture
def playlist_creator(tmp_path: Path) -> PlaylistCreator:
    conf = AceReStreamerConf()

    return PlaylistCreator(
        instance_path=tmp_path,
        config=conf,
    )


@pytest.fixture
def stream_name_processor(tmp_path: Path) -> StreamNameProcessor:
    processor = StreamNameProcessor()
    processor.load_config(
        instance_path=tmp_path,
        content_id_infohash_name_overrides={},
        category_mapping={},
    )
    return processor


def get_playlist_content(function_name: str, number: int) -> str:
    m3u_file = _M3U_TEST_DATA_DIR / f"{function_name}_{number}.m3u8"
    return m3u_file.read_text()


def test_playlist_creator_init(playlist_creator: PlaylistCreator, tmp_path: Path) -> None:
    assert playlist_creator._instance_path == tmp_path
    assert playlist_creator.playlist_name == "acerestreamer"


@pytest.mark.asyncio
async def test_infohash_last_scraped_time(
    tmp_path: Path,
    stream_name_processor: StreamNameProcessor,
    playlist_creator: PlaylistCreator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    frame = inspect.currentframe()
    function_name = frame.f_code.co_name if frame else "unknown_function"
    infohash_playlist_path = tmp_path / "playlists" / "acerestreamer-infohash-main.m3u"

    iptv_scraper = IPTVStreamScraper()
    iptv_scraper.load_config(
        instance_path=tmp_path,
        stream_name_processor=stream_name_processor,
    )
    scrape_site = ScrapeSiteIPTV(
        name="Test IPTV Site",
        url=HttpUrl("http://pytest.internal/lists/playlist.m3u"),
    )

    # First scrape - should find streams
    found_streams = await iptv_scraper.parse_m3u_content(
        content=get_playlist_content(function_name, 1),
        site=scrape_site,
    )
    assert len(found_streams) == 2
    await playlist_creator._create_playlists(new_streams=found_streams)

    files = list((tmp_path / "playlists").glob("*.m3u"))
    for file in files:
        assert file.read_text().strip() != ""
    assert infohash_playlist_path.read_text().strip() != "#EXTM3U", "Infohash playlist should not be empty"
    assert 'x-last-found="0"' in infohash_playlist_path.read_text()  # This should be here since its freshly scraped

    # Second scrape - should find no streams, load local cache
    found_streams = await iptv_scraper.parse_m3u_content(
        content=get_playlist_content(function_name, 2),
        site=scrape_site,
    )
    assert len(found_streams) == 0  # No streams found this time

    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await playlist_creator._create_playlists(new_streams=found_streams)

    assert "No existing streams found in existing playlists" not in caplog.text
    assert "Loaded 2 existing streams from existing playlists" in caplog.text

    files = list((tmp_path / "playlists").glob("*.m3u"))
    for file in files:
        assert file.read_text().strip() != ""
    assert infohash_playlist_path.read_text().strip() != "#EXTM3U", (
        "Infohash playlist should not be empty after second scrape"
    )
    assert 'x-last-found="0"' not in infohash_playlist_path.read_text()

    # Third scrape - now there is a last_scraped_time update
    found_streams = await iptv_scraper.parse_m3u_content(
        content=get_playlist_content(function_name, 2),
        site=scrape_site,
    )
    assert len(found_streams) == 0  # No streams found this time

    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await playlist_creator._create_playlists(new_streams=found_streams)

    assert "No existing streams found in existing playlists" not in caplog.text
    assert "Loaded 2 existing streams from existing playlists" in caplog.text
    assert 'x-last-found="0"' not in infohash_playlist_path.read_text()

    # Fourth scrape - the streams are back
    found_streams = await iptv_scraper.parse_m3u_content(
        content=get_playlist_content(function_name, 3),
        site=scrape_site,
    )
    for stream in found_streams:  # These streams are freshly scraped, simulate _scrape_iptv_playlist
        stream.last_scraped_time = datetime.now(tz=OUR_TIMEZONE)

    assert len(found_streams) == 2
    await playlist_creator._create_playlists(new_streams=found_streams)

    assert 'x-last-found="0"' in infohash_playlist_path.read_text()
