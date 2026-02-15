from acere.core.config import AceReStreamerConf


def test_urls_as_strings() -> None:
    """Test that URL configurations are properly converted to strings."""
    settings = AceReStreamerConf()

    ace_address_str = settings.app.ace_address.encoded_string()

    assert isinstance(ace_address_str, str)
    assert ace_address_str.endswith("/")

def test_external_url_as_string() -> None:
    """Test that EXTERNAL_URL is properly converted to a string."""
    settings = AceReStreamerConf()

    external_url_str = settings.EXTERNAL_URL

    assert isinstance(external_url_str, str)
    assert not external_url_str.endswith("/")

