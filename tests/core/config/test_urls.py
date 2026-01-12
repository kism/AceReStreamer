
from acere.core.config import AceReStreamerConf


def test_urls_as_strings() -> None:
    """Test that URL configurations are properly converted to strings."""
    settings = AceReStreamerConf()

    ace_address_str = settings.app.ace_address.encoded_string()

    assert isinstance(ace_address_str, str)
    assert ace_address_str.endswith("/")
