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
        sites_found_on=["Test Site"],
        content_id=get_random_content_id(),
        title="Test Stream",
        infohash=get_random_content_id(),
        tvg_id="test_tvg_id",
    )


@pytest.mark.asyncio
async def test_scraper_main(tmp_path: Path) -> None:
    """Test the AceScraper main functionality."""
    scraper = AceScraper()

    scraper.start_scrape_thread()
    for thread in scraper._threads:
        thread.join(timeout=1)

    steam_api_example = get_stream()
    content_id = steam_api_example.content_id
    scraper._streams = {content_id: steam_api_example}
