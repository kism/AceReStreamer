from acere.core.config.scraper import (
    AceScrapeConf,
    ScrapeSiteAPI,
    ScrapeSiteHTML,
    ScrapeSiteIPTV,
)


def test_add_iptv_source() -> None:
    """Test adding an IPTV source."""
    config = AceScrapeConf()
    initial_count = len(config.iptv_m3u8)

    new_site = ScrapeSiteIPTV(type="iptv", name="test-iptv", url="http://ace.pytest.internal/playlist.m3u8")
    success, message = config.add_iptv_source(new_site)

    assert success is True
    assert message == "Source added"
    assert len(config.iptv_m3u8) == initial_count + 1


def test_add_html_source() -> None:
    """Test adding an HTML source."""
    config = AceScrapeConf()
    initial_count = len(config.html)

    new_site = ScrapeSiteHTML(type="html", name="test-html", url="http://ace.pytest.internal")
    success, message = config.add_html_source(new_site)

    assert success is True
    assert message == "Source added"
    assert len(config.html) == initial_count + 1


def test_add_api_source() -> None:
    """Test adding an API source."""
    config = AceScrapeConf()
    initial_count = len(config.api)

    new_site = ScrapeSiteAPI(type="api", name="test-api", url="http://ace.pytest.internal/api")
    success, message = config.add_api_source(new_site)

    assert success is True
    assert message == "Source added"
    assert len(config.api) == initial_count + 1


def test_add_duplicate_source_fails() -> None:
    """Test that adding a duplicate source fails."""
    config = AceScrapeConf()

    new_site = ScrapeSiteIPTV(type="iptv", name="test-duplicate", url="http://ace.pytest.internal/playlist.m3u8")
    success, _ = config.add_iptv_source(new_site)
    assert success is True

    # Try to add the same source again
    success, message = config.add_iptv_source(new_site)
    assert success is False
    assert "Duplicate" in message


def test_remove_iptv_source() -> None:
    """Test removing an IPTV source."""
    config = AceScrapeConf()

    new_site = ScrapeSiteIPTV(type="iptv", name="test-remove-iptv", url="http://ace.pytest.internal/playlist.m3u8")
    config.add_iptv_source(new_site)
    initial_count = len(config.iptv_m3u8)

    success, message = config.remove_source("test-remove-iptv")

    assert success is True
    assert message == "Source removed"
    assert len(config.iptv_m3u8) == initial_count - 1


def test_remove_html_source() -> None:
    """Test removing an HTML source."""
    config = AceScrapeConf()

    new_site = ScrapeSiteHTML(type="html", name="test-remove-html", url="http://ace.pytest.internal")
    config.add_html_source(new_site)
    initial_count = len(config.html)

    success, message = config.remove_source("test-remove-html")

    assert success is True
    assert message == "Source removed"
    assert len(config.html) == initial_count - 1


def test_remove_api_source() -> None:
    """Test removing an API source."""
    config = AceScrapeConf()

    new_site = ScrapeSiteAPI(type="api", name="test-remove-api", url="http://ace.pytest.internal/api")
    config.add_api_source(new_site)
    initial_count = len(config.api)

    success, message = config.remove_source("test-remove-api")

    assert success is True
    assert message == "Source removed"
    assert len(config.api) == initial_count - 1


def test_update_source_rename() -> None:
    """Test updating a source in place, including a rename."""
    config = AceScrapeConf()

    new_site = ScrapeSiteIPTV(type="iptv", name="test-update", url="http://ace.pytest.internal/playlist.m3u8")
    config.add_iptv_source(new_site)

    renamed = ScrapeSiteIPTV(type="iptv", name="test-renamed", url="http://ace.pytest.internal/other.m3u8")
    success, message = config.update_source("test-update", renamed)

    assert success is True
    assert message == "Source updated"
    assert [site.name for site in config.iptv_m3u8].count("test-update") == 0
    assert [site.name for site in config.iptv_m3u8].count("test-renamed") == 1


def test_update_source_type_change() -> None:
    """Test updating a source to a different type moves it between lists."""
    config = AceScrapeConf()

    new_site = ScrapeSiteIPTV(type="iptv", name="test-type-change", url="http://ace.pytest.internal/playlist.m3u8")
    config.add_iptv_source(new_site)
    iptv_count = len(config.iptv_m3u8)
    html_count = len(config.html)

    as_html = ScrapeSiteHTML(type="html", name="test-type-change", url="http://ace.pytest.internal")
    success, _ = config.update_source("test-type-change", as_html)

    assert success is True
    assert len(config.iptv_m3u8) == iptv_count - 1
    assert len(config.html) == html_count + 1


def test_update_nonexistent_source() -> None:
    """Test updating a source that doesn't exist."""
    config = AceScrapeConf()

    new_site = ScrapeSiteIPTV(type="iptv", name="test-missing", url="http://ace.pytest.internal/playlist.m3u8")
    success, message = config.update_source("test-missing", new_site)

    assert success is False
    assert "Source not found" in message


def test_update_source_duplicate_name_fails() -> None:
    """Test that renaming a source onto another existing name fails and changes nothing."""
    config = AceScrapeConf()

    config.add_iptv_source(ScrapeSiteIPTV(type="iptv", name="test-dup-a", url="http://ace.pytest.internal/a.m3u8"))
    config.add_iptv_source(ScrapeSiteIPTV(type="iptv", name="test-dup-b", url="http://ace.pytest.internal/b.m3u8"))

    clashing = ScrapeSiteIPTV(type="iptv", name="test-dup-b", url="http://ace.pytest.internal/c.m3u8")
    success, message = config.update_source("test-dup-a", clashing)

    assert success is False
    assert "Duplicate" in message
    assert [site.name for site in config.iptv_m3u8].count("test-dup-a") == 1


def test_remove_nonexistent_source() -> None:
    """Test removing a source that doesn't exist."""
    config = AceScrapeConf()

    success, message = config.remove_source("nonexistent-source")

    assert success is False
    assert "Source not found" in message
