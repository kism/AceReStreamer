from pathlib import Path

import pytest
from pydantic import HttpUrl

from acere.core.config import HTMLScraperFilter, ScrapeSiteHTML, TitleFilter
from acere.services.scraper.html import HTMLStreamScraper
from acere.services.scraper.name_processor import StreamNameProcessor

from . import SCRAPER_TEST_SITES


@pytest.fixture
def name_processor(tmp_path: Path) -> StreamNameProcessor:
    """Fixture providing a configured StreamNameProcessor."""
    processor = StreamNameProcessor()
    processor.load_config(
        instance_path=tmp_path,
        name_replacements={},
        category_mapping={},
    )
    return processor


@pytest.fixture
def scraper(tmp_path: Path, name_processor: StreamNameProcessor) -> HTMLStreamScraper:
    """Fixture providing a configured HTMLStreamScraper."""
    scraper = HTMLStreamScraper()
    scraper.load_config(
        instance_path=tmp_path,
        stream_name_processor=name_processor,
    )
    return scraper


def _get_test_sites() -> dict[str, ScrapeSiteHTML]:
    return {
        "site1.html": ScrapeSiteHTML(
            type="html",
            name="Test Site 1",
            url=HttpUrl("http://pytest.internal/site1.html"),
            html_filter=HTMLScraperFilter(
                target_class="column_title",
                check_sibling=True,
            ),
        ),
        "site2.html": ScrapeSiteHTML(
            type="html",
            name="Test Site 2",
            url=HttpUrl("http://pytest.internal/site2.html"),
            html_filter=HTMLScraperFilter(
                target_class="streamtext",
                check_sibling=True,
            ),
            title_filter=TitleFilter(
                regex_postprocessing="Server \\d+: ",
            ),
        ),
        "site3.html": ScrapeSiteHTML(
            type="html",
            name="Test Site 3",
            url=HttpUrl("http://pytest.internal/site3.html"),
            html_filter=HTMLScraperFilter(
                target_class="",
                check_sibling=False,
            ),
            title_filter=TitleFilter(exclude_words=["beelzebub"]),
        ),
        "site4.html": ScrapeSiteHTML(
            type="html",
            name="Test Site 4",
            url=HttpUrl("http://pytest.internal/site4.html"),
            html_filter=HTMLScraperFilter(
                target_class="streamtext2",
                check_sibling=True,
            ),
            title_filter=TitleFilter(
                regex_postprocessing="Server \\d+: ",
            ),
        ),
    }


def _common_title_check(title: str) -> None:
    """Common checks for titles in tests."""
    assert "000000000000" not in title, f"Placeholder title found: {title}"
    assert len(title) != 40, "Title should not the the content_id"


async def test_site1(scraper: HTMLStreamScraper, caplog: pytest.LogCaptureFixture) -> None:
    """Test HTML scraper with site1.html - basic scraping with column_title class."""
    site = _get_test_sites()["site1.html"]
    site_html_str = (SCRAPER_TEST_SITES / "site1.html").read_text(encoding="utf-8")
    scraper.scraper_cache.save_to_cache(site.url, site_html_str)

    with caplog.at_level("DEBUG"):
        results = await scraper._scrape_site(site)

    assert len(results) > 0, "No streams found in site1"

    titles = [result.title for result in results]

    for title in titles:
        _common_title_check(title)

    assert "SMPTE SD ECR-1-1978" in titles
    assert "SMPTE RP 219:2002" in titles


async def test_site2(scraper: HTMLStreamScraper, caplog: pytest.LogCaptureFixture) -> None:
    """Test HTML scraper with site2.html - includes regex postprocessing to remove 'Server X: ' prefix."""
    site = _get_test_sites()["site2.html"]
    site_html_str = (SCRAPER_TEST_SITES / "site2.html").read_text(encoding="utf-8")
    scraper.scraper_cache.save_to_cache(site.url, site_html_str)

    with caplog.at_level("DEBUG"):
        results = await scraper._scrape_site(site)

    assert len(results) > 0, "No streams found in site2"

    titles = [result.title for result in results]

    for title in titles:
        _common_title_check(title)
        assert not title.startswith("Server "), f"Title filter failed to remove 'Server ' prefix: {title}"

    assert any(result.title == "Big Buck Bunny" for result in results), (
        "Stream name postprocessing failed to clean up title properly"
    )


async def test_site3(scraper: HTMLStreamScraper, caplog: pytest.LogCaptureFixture) -> None:
    """Test HTML scraper with site3.html - includes exclude_words filter and name truncation."""
    site = _get_test_sites()["site3.html"]
    site_html_str = (SCRAPER_TEST_SITES / "site3.html").read_text(encoding="utf-8")
    scraper.scraper_cache.save_to_cache(site.url, site_html_str)

    with caplog.at_level("DEBUG"):
        results = await scraper._scrape_site(site)

    assert len(results) > 0, "No streams found in site3"

    titles = [result.title for result in results]

    for title in titles:
        _common_title_check(title)
        assert "beelzebub" not in title, f"Title filter failed to exclude 'beelzebub': {title}"

    assert any(result.title == "LONG STREAM NAME IS VERY ABSOLUTELY WAY TOO LONG L" for result in results), (
        "Long stream name was not truncated properly"
    )


async def test_site4(scraper: HTMLStreamScraper, caplog: pytest.LogCaptureFixture) -> None:
    """Test HTML scraper with site4.html - streamtext2 class with regex postprocessing."""
    site = _get_test_sites()["site4.html"]
    site_html_str = (SCRAPER_TEST_SITES / "site4.html").read_text(encoding="utf-8")
    scraper.scraper_cache.save_to_cache(site.url, site_html_str)

    with caplog.at_level("DEBUG"):
        results = await scraper._scrape_site(site)

    assert len(results) > 0, "No streams found in site4"

    titles = [result.title for result in results]

    for title in titles:
        _common_title_check(title)
        assert not title.startswith("Server "), f"Title filter failed to remove 'Server ' prefix: {title}"
