from typing import TYPE_CHECKING

import pytest
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
