from typing import TYPE_CHECKING

import pytest
from pydantic import HttpUrl

from acere.core.config import AceScrapeConf
from acere.services.scraper import AceScraper
from acere.services.scraper.models import FoundAceStream
from tests.test_utils.ace import get_random_content_id

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object

_EXTERNAL_URL = "http://example.com/"
_ACE_URL: HttpUrl = HttpUrl("http://localhost:6878/")


def get_test_config() -> AceScrapeConf:
    """Get a test configuration for AceScraper."""
    return AceScrapeConf()


def get_stream() -> FoundAceStream:
    """Get a test FoundAceStream object."""
    return FoundAceStream(
        site_names=["Test Site"],
        content_id=get_random_content_id(),
        title="Test Stream",
        quality=50,
        infohash=get_random_content_id(),
        tvg_id="test_tvg_id",
    )


@pytest.mark.asyncio
async def test_scraper_main(tmp_path: Path) -> None:
    """Test the AceScraper main functionality."""
    scraper = AceScraper()
    scraper.load_config(
        ace_scrape_conf=get_test_config(),
        epg_conf_list=[],
        instance_path=tmp_path,
        external_url=_EXTERNAL_URL,
        ace_url=_ACE_URL,
    )

    scraper.start_scrape_thread()
    for thread in scraper._scrape_threads:
        thread.join(timeout=1)

    steam_api_example = get_stream()
    content_id = steam_api_example.content_id
    scraper.streams = {content_id: steam_api_example}

    # Gets
    assert scraper.get_stream_by_content_id_api(content_id)
    assert len(scraper.get_scraper_sources_flat_api()) == 0, (
        "get_scraper_sources_flat_api() Expected zero scraper sources"
    )
    assert len(scraper.get_stream_list_api()) == 1, "get_stream_list_api() Expected one stream"
    assert scraper.get_streams_health() != {}

    xc_id = scraper._content_id_xc_id_mapping.get_xc_id(content_id)
    assert scraper.get_content_id_by_xc_id(xc_id)
    assert scraper.get_content_id_by_tvg_id("test_tvg_id")

    assert scraper.get_streams_as_iptv(token="") is not None
    assert len(scraper.get_streams_as_iptv_xc(xc_category_filter=None, token="")) == 1

    # Quality
    scraper.increment_quality(content_id)
