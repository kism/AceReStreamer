import pytest

from acere.core.config import AceReStreamerConf
from acere.core.config.app import AppConf


def test_default_urls_as_strings() -> None:
    """Test that URL configurations are properly converted to strings."""
    settings = AceReStreamerConf()

    ace_address_str = settings.app.ace_address.encoded_string()

    assert isinstance(ace_address_str, str)
    assert ace_address_str.endswith("/")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://localhost:6878/", "http://localhost:6878/"),
        ("http://localhost:6878", "http://localhost:6878/"),
    ],
)
def test_strip_trailing_slash(url: str, expected: str) -> None:
    """Test that the strip_trailing_slash function correctly removes trailing slashes."""
    app_config = AppConf(
        ace_address=url,  # type: ignore[arg-type]
    )

    assert app_config.ace_address.encoded_string() == expected


def test_default_external_url_as_string() -> None:
    """Test that EXTERNAL_URL is properly converted to a string."""
    settings = AceReStreamerConf()

    external_url_str = settings.EXTERNAL_URL

    assert isinstance(external_url_str, str)
    assert not external_url_str.endswith("/")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://ace.pytest.internal:8000/", "http://ace.pytest.internal:8000"),
        ("http://ace.pytest.internal:8000", "http://ace.pytest.internal:8000"),
        ("http://ace.pytest.internal", "http://ace.pytest.internal"),
        ("http://ace.pytest.internal/", "http://ace.pytest.internal"),
        ("https://ace.pytest.internal", "https://ace.pytest.internal"),
        ("https://ace.pytest.internal/", "https://ace.pytest.internal"),
    ],
)
def test_external_url_strip_trailing_slash(url: str, expected: str) -> None:
    """Test that the EXTERNAL_URL configuration correctly removes trailing slashes."""
    settings = AceReStreamerConf(
        EXTERNAL_URL=url,
    )

    assert expected == settings.EXTERNAL_URL
