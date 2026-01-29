from pydantic import HttpUrl

from acere.core.config.scraper import ScrapeSiteGeneric


def test_slugify() -> None:
    """Test the slugify method of ScrapeSiteGeneric."""
    url_str = "http://example.com/some Path/With Special_Chars?)"

    scrape_site = ScrapeSiteGeneric(
        name="",
        type="html",
        url=HttpUrl(url_str),
    )
    assert scrape_site.name == "http-example-com-some-path-with-special-chars"
