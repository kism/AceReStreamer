from typing import TYPE_CHECKING

import pytest
from pydantic import HttpUrl
from sqlmodel import create_engine

from acere.database.handlers.acestreams import AceStreamDBHandler
from acere.database.models import AceStreamDBEntry
from acere.services.scraper.models import FoundAceStream
from tests.test_utils.ace import get_random_content_id

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object


@pytest.fixture
def acestream_db_handler(tmp_path: Path) -> AceStreamDBHandler:
    """Fixture for AceStreamDBHandler."""
    test_engine = create_engine(f"sqlite:///{tmp_path / 'test_acestreams.db'}", echo=False)

    return AceStreamDBHandler(test_engine=test_engine)


@pytest.fixture(autouse=True)
def set_external_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fixture to set EXTERNAL_URL for tests."""
    monkeypatch.setattr("acere.instances.config.settings.EXTERNAL_URL", "http://localhost:8000/")


def test_init(acestream_db_handler: AceStreamDBHandler, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test initialization of AceStreamDBHandler."""
    handler = acestream_db_handler

    assert handler.delete_by_content_id("nonexistent") is False
    assert handler.get_by_content_id("nonexistent") is None
    assert handler.get_content_id_from_infohash("nonexistent") is None
    assert handler.get_streams() == []
    assert handler.get_streams_cached() == []
    assert handler.get_content_id_by_tvg_id("nonexistent") is None
    assert handler.get_content_id_by_xc_id(1) is None
    assert handler.get_xc_id_by_content_id("nonexistent") is None
    assert "#EXTM3U" in handler.get_streams_as_iptv(token="")
    assert len(handler.get_streams_as_iptv_xc(xc_category_filter=None)) == 0
    handler._mark_alternate_streams([])


def test_add_and_delete(acestream_db_handler: AceStreamDBHandler) -> None:
    """Test adding and deleting entries in AceStreamDBHandler."""
    handler = acestream_db_handler
    assert handler.get_streams() == []

    content_id = get_random_content_id()
    stream = FoundAceStream(
        content_id=content_id,
        title="Test Stream",
        tvg_id="test.tvg.id",
        sites_found_on=["TestSite"],
    )

    handler.update_stream(stream)
    retrieved_stream = handler.get_by_content_id(content_id)
    assert retrieved_stream is not None
    assert retrieved_stream.title == "Test Stream"

    stream.title = "Updated Test Stream"
    handler.update_stream(stream)
    updated_stream = handler.get_by_content_id(content_id)
    assert updated_stream is not None
    assert updated_stream.title == "Updated Test Stream"

    # Do some normal things
    assert handler.get_content_id_from_infohash(content_id) is None  # Content id is not an infohash
    assert handler.get_streams() != []
    assert handler.get_streams_cached() != []
    assert handler.get_content_id_by_tvg_id("test.tvg.id") is not None
    assert handler.get_content_id_by_xc_id(1) == content_id
    assert handler.get_xc_id_by_content_id(content_id) == 1
    assert "#EXTM3U" in handler.get_streams_as_iptv(token="")
    assert len(handler.get_streams_as_iptv_xc(xc_category_filter=None)) == 1
    handler._mark_alternate_streams([])

    # Delete
    assert handler.delete_by_content_id(content_id) is True
    assert handler.get_by_content_id(content_id) is None


def test_mark_alternate_streams(acestream_db_handler: AceStreamDBHandler) -> None:
    """Test the _mark_alternate_streams method."""
    handler = acestream_db_handler

    stream1 = AceStreamDBEntry(
        id=1,
        content_id=get_random_content_id(),
        title="Duplicate Stream",
        tvg_id="tvg.id.1",
    )
    stream2 = AceStreamDBEntry(
        id=2,
        content_id=get_random_content_id(),
        title="Duplicate Stream",
        tvg_id="tvg.id.2",
    )
    stream3 = AceStreamDBEntry(
        id=3,
        content_id=get_random_content_id(),
        title="Unique Stream",
        tvg_id="tvg.id.3",
    )
    streams = [stream1, stream2, stream3]

    handler._mark_alternate_streams(streams)

    titles = [stream.title for stream in streams]
    assert "Duplicate Stream #1" in titles
    assert "Duplicate Stream #2" in titles
    assert "Unique Stream" in titles


def test_get_streams_as_iptv_url_validation(
    acestream_db_handler: AceStreamDBHandler,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that get_streams_as_iptv generates valid URLs that can be validated with HttpUrl."""
    handler = acestream_db_handler

    # Test with URL that has a port (the original bug case)
    monkeypatch.setattr("acere.instances.config.settings.EXTERNAL_URL", "http://192.168.100.130:5100")

    # Add test streams
    content_id_1 = get_random_content_id()
    stream_1 = FoundAceStream(
        content_id=content_id_1,
        title="Test Stream 1",
        tvg_id="test.stream.1",
        sites_found_on=["TestSite"],
    )
    handler.update_stream(stream_1)

    content_id_2 = get_random_content_id()
    stream_2 = FoundAceStream(
        content_id=content_id_2,
        title="Test Stream 2",
        tvg_id="test.stream.2",
        sites_found_on=["TestSite"],
    )
    handler.update_stream(stream_2)

    # Get IPTV without token
    m3u8_content = handler.get_streams_as_iptv(token="")

    # Verify M3U8 header exists
    assert m3u8_content.startswith("#EXTM3U")

    # Verify EPG URL is valid and in the header
    assert "x-tvg-url=" in m3u8_content
    assert "http://192.168.100.130:5100/epg" in m3u8_content

    # Extract and validate EPG URL from header
    epg_url_start = m3u8_content.find('x-tvg-url="') + len('x-tvg-url="')
    epg_url_end = m3u8_content.find('"', epg_url_start)
    epg_url_str = m3u8_content[epg_url_start:epg_url_end]
    epg_url = HttpUrl(epg_url_str)  # Should not raise ValidationError
    assert str(epg_url) == "http://192.168.100.130:5100/epg"

    # Verify HLS stream URLs are valid
    assert f"http://192.168.100.130:5100/hls/{content_id_1}" in m3u8_content
    assert f"http://192.168.100.130:5100/hls/{content_id_2}" in m3u8_content

    # Validate each HLS URL can be parsed as HttpUrl
    hls_url_1 = HttpUrl(f"http://192.168.100.130:5100/hls/{content_id_1}")
    hls_url_2 = HttpUrl(f"http://192.168.100.130:5100/hls/{content_id_2}")
    assert str(hls_url_1) == f"http://192.168.100.130:5100/hls/{content_id_1}"
    assert str(hls_url_2) == f"http://192.168.100.130:5100/hls/{content_id_2}"

    # Test with token
    m3u8_with_token = handler.get_streams_as_iptv(token="test_token")
    assert f"http://192.168.100.130:5100/hls/{content_id_1}?token=test_token" in m3u8_with_token
    assert f"http://192.168.100.130:5100/hls/{content_id_2}?token=test_token" in m3u8_with_token

    # Test with different EXTERNAL_URL formats
    # URL without port
    monkeypatch.setattr("acere.instances.config.settings.EXTERNAL_URL", "http://ace.pytest.internal")
    m3u8_no_port = handler.get_streams_as_iptv(token="")
    assert "http://ace.pytest.internal/epg" in m3u8_no_port
    assert f"http://ace.pytest.internal/hls/{content_id_1}" in m3u8_no_port

    # HTTPS URL with port
    monkeypatch.setattr("acere.instances.config.settings.EXTERNAL_URL", "https://secure.ace.pytest.internal:8443")
    m3u8_https = handler.get_streams_as_iptv(token="")
    assert "https://secure.ace.pytest.internal:8443/epg" in m3u8_https
    assert f"https://secure.ace.pytest.internal:8443/hls/{content_id_1}" in m3u8_https
