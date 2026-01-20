from datetime import datetime
from pathlib import Path

import pytest

from acere.constants import OUR_TIMEZONE
from acere.core.config import EPGInstanceConf
from acere.services.epg.epg import EPG, ONE_WEEK
from acere.services.epg.handler import EPGHandler

EPG_TEST_XML_PATH = Path(__file__).parent / "epgs" / "test.xml"


@pytest.fixture
def epg_conf() -> EPGInstanceConf:
    """Fixture for EPGInstanceConf."""
    return EPGInstanceConf(
        url="http://example.com/epg.xml",  # type: ignore[arg-type]
        format="xml",
        tvg_id_overrides={},
        region_code="AU",
    )


@pytest.fixture
def epg_handler(epg_conf: EPGInstanceConf, monkeypatch: pytest.MonkeyPatch) -> EPGHandler:
    epg = EPG(epg_conf)
    epg.saved_file_path = EPG_TEST_XML_PATH

    handler = EPGHandler()
    monkeypatch.setattr(handler, "_update_epgs", lambda: None)
    handler.load_config([epg_conf])
    handler.epgs = [epg]
    return handler


def test_epg_object_initialization(epg_conf: EPGInstanceConf) -> None:
    """Test EPG object initialization."""
    epg = EPG(epg_conf)
    assert epg.get_epg_etree_normalised() is None
    assert epg.get_time_since_last_update() == ONE_WEEK
    assert epg.get_time_until_next_update().total_seconds() == 0
    assert epg._time_to_update() is True


def test_epg_object_with_data(epg_conf: EPGInstanceConf) -> None:
    """Test EPG object with actual data."""
    epg = EPG(epg_conf)
    epg.saved_file_path = EPG_TEST_XML_PATH
    epg.last_updated = datetime.now(tz=OUR_TIMEZONE)

    etree = epg.get_epg_etree_normalised()
    assert etree is not None


def test_epg_handler_initialization(epg_handler: EPGHandler) -> None:
    """Test EPGHandler initialization."""
    assert epg_handler.epgs[0].get_epg_etree_normalised() is not None
    epg_handler.add_tvg_ids(["channel1.au", "channel2.au"])
    epg_handler._condense_epgs()
