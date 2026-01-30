"""Test the scraper CLI's ability to load app config from arguments."""

import random
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import HttpUrl

from acere.cli.scraper.__main__ import async_main
from acere.core.config import AceReStreamerConf
from acere.core.config.scraper import ScrapeSiteIPTV
from tests.test_utils.aiohttp import FakeSession


@pytest.mark.asyncio
async def test_async_main_with_app_config(tmp_path: Path) -> None:
    """Test that the correct config file and playlist are used in cli mode."""
    # Create a config file with scraper settings
    random_playlist_str = str(random.randbytes(8).hex())
    random_dir_str = str(random.randbytes(8).hex())

    instance_dir = tmp_path / random_dir_str
    instance_dir.mkdir(parents=True, exist_ok=True)
    config_path = instance_dir / "test_config.json"

    # Read test m3u8 file
    m3u8_file = Path(__file__).parent / "m3u8" / "test_infohash_last_scraped_time_1.m3u8"
    m3u8_content = m3u8_file.read_text()

    # Generate config
    config = AceReStreamerConf.force_load_defaults()
    config.scraper.playlist_name = f"test-playlist-{random_playlist_str}"
    config.scraper.tvg_logo_external_url = HttpUrl("http://ace.pytest.internal/logos/")
    config.scraper.adhoc_playlist_external_url = HttpUrl("http://ace.pytest.internal/playlists/")
    config.scraper.iptv_m3u8.append(
        ScrapeSiteIPTV(name="Test Site", url=HttpUrl("http://ace.pytest.internal/test.m3u"))
    )

    config.write_config(config_path)

    # Mock sys.argv to simulate CLI arguments
    test_args = ["scraper", "--app-config", str(config_path)]

    # Create fake aiohttp session with m3u8 content
    fake_responses = {
        "http://ace.pytest.internal/test.m3u": {
            "status": 200,
            "data": m3u8_content,
        }
    }

    def fake_client_session(*_: Any, **__: Any) -> FakeSession:
        return FakeSession(fake_responses)  # type: ignore[arg-type]

    # Mock aiohttp.ClientSession to return our fake session in the scraper module
    # Also need to patch the global settings object that the scrapers use
    with (
        patch.object(sys, "argv", test_args),
        patch("acere.services.scraper.iptv.aiohttp.ClientSession", fake_client_session),
    ):
        await async_main()

        # Verify that playlists were created
        playlists_dir = instance_dir / "playlists"
        assert playlists_dir.exists()

        # Check that the infohash playlist was created with content
        infohash_playlist = playlists_dir / f"{config.scraper.playlist_name}-infohash-main.m3u"
        assert infohash_playlist.exists()
        playlist_content = infohash_playlist.read_text()
        assert "0000000000000000000000000000000000000001" in playlist_content
        assert "0000000000000000000000000000000000000002" in playlist_content
