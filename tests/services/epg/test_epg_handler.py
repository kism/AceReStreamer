import io
from compression import gzip
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal

import pytest
from lxml import etree

from acere.constants import OUR_TIMEZONE
from acere.core.config import EPGInstanceConf
from acere.services.epg.epg import EPG, ONE_WEEK
from acere.services.epg.handler import EPGHandler
from tests.test_utils.aiohttp import FakeSession
from tests.test_utils.epg import generate_future_program_xml

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture
else:
    MockerFixture = object
    Path = object


@pytest.fixture
def epg_conf() -> EPGInstanceConf:
    """Fixture for EPGInstanceConf."""
    return EPGInstanceConf(
        url="http://example.com/epg.xml",  # type: ignore[arg-type]
        format="xml",
        tvg_id_overrides={},
    )


@pytest.fixture
def epg_test_xml_path(tmp_path: Path) -> Path:
    """Fixture for EPG test XML file path."""
    epg_xml_path = tmp_path / "test_epg.xml"
    epg_xml_path.write_bytes(etree.tostring(generate_future_program_xml()))
    return epg_xml_path


@pytest.fixture
def epg_handler(epg_conf: EPGInstanceConf, monkeypatch: pytest.MonkeyPatch, epg_test_xml_path: Path) -> EPGHandler:
    epg = EPG(epg_conf)
    epg.saved_file_path = epg_test_xml_path

    handler = EPGHandler()
    monkeypatch.setattr(handler, "_update_epgs", lambda: None)
    handler.load_config([epg_conf])
    handler._epgs = [epg]
    return handler


def test_epg_object_initialization(epg_conf: EPGInstanceConf) -> None:
    """Test EPG object initialization."""
    epg = EPG(epg_conf)
    assert epg.get_epg_etree_normalised() is None
    assert epg.get_time_since_last_update() == ONE_WEEK
    assert epg.get_time_until_next_update().total_seconds() == 0
    assert epg._time_to_update() is True


def test_epg_object_with_data(epg_conf: EPGInstanceConf, epg_test_xml_path: Path) -> None:
    """Test EPG object with actual data."""
    epg = EPG(epg_conf)
    epg.saved_file_path = epg_test_xml_path
    epg.last_updated = datetime.now(tz=OUR_TIMEZONE)

    etree = epg.get_epg_etree_normalised()
    assert etree is not None


def test_epg_handler_initialization(epg_handler: EPGHandler) -> None:
    """Test EPGHandler initialization."""
    assert epg_handler._epgs[0].get_epg_etree_normalised() is not None
    epg_handler.add_tvg_ids(["channel1.au", "channel2.au"])
    epg_handler._condense_epgs()


@pytest.mark.parametrize("epg_format", ["xml", "xml.gz"])
@pytest.mark.asyncio
async def test_epg_update(
    epg_conf: EPGInstanceConf,
    mocker: MockerFixture,
    tmp_path: Path,
    epg_format: Literal["xml", "xml.gz"],
) -> None:
    """Test EPG update method with aiohttp mock."""
    # Generate XML data programmatically to ensure consistency
    original_xml_data = etree.tostring(generate_future_program_xml(), encoding="utf-8", xml_declaration=True)

    if epg_format == "xml.gz":
        # For gzipped format, compress the XML for the mock response
        with io.BytesIO() as byte_stream:
            with gzip.GzipFile(fileobj=byte_stream, mode="wb") as gz_file:
                gz_file.write(original_xml_data)
            test_xml_data = byte_stream.getvalue()
    else:
        test_xml_data = original_xml_data

    # Create a mock aiohttp session
    fake_session = FakeSession(
        responses={
            "http://example.com/epg.xml": {
                "status": 200,
                "data": test_xml_data,
            }
        }
    )

    # Mock aiohttp.ClientSession to return our fake session
    mocker.patch("aiohttp.ClientSession", return_value=fake_session)

    # Create EPG instance with a temporary path
    epg = EPG(epg_conf)
    epg.format = epg_format
    epg.saved_file_path = tmp_path / "test_epg.xml"

    # Verify initial state
    assert epg.last_updated is None, "Expected last_updated to be None before update"
    assert epg._time_to_update() is True, "Expected _time_to_update to be True before update"

    # Call update
    result = await epg.update()

    # Verify update was successful
    assert result is True, "Expected update to return True"
    assert epg.last_updated is not None, "Expected last_updated to be set after update"
    assert epg.saved_file_path.exists(), "Expected saved_file_path to exist after update"
    # The saved file should always contain uncompressed XML data
    assert epg.saved_file_path.read_bytes() == original_xml_data, "Saved file content does not match expected XML data"

    # Verify EPG data can be parsed
    tree = epg.get_epg_etree_normalised()
    assert tree is not None
    channels = tree.findall("channel")
    assert len(channels) == 2

    # Update again immediately - should not update (not enough time passed)
    result = await epg.update()
    assert result is False

    assert epg.get_time_since_last_update() < ONE_WEEK
    assert epg.get_time_until_next_update() > timedelta(0)


@pytest.mark.asyncio
async def test_epg_update_and_get(
    epg_handler: EPGHandler,
    mocker: MockerFixture,
) -> None:
    """Test EPGHandler update_all_epgs and get_combined_epg."""
    # Mock the update method of EPG to always return True
    mocker.patch.object(EPG, "update", return_value=True)

    assert epg_handler.get_condensed_epg() is not None
    assert epg_handler.get_epgs_api() is not None
    assert epg_handler.get_current_program("invalid") == ("", "")
    assert epg_handler.get_tvg_epg_mappings() is not None
