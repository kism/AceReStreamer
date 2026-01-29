from acere.core.config.scraper import TitleFilter


def test_title_filter_postprocessing() -> None:
    """Test the postprocessing of titles using TitleFilter."""
    # Empty elements are removed from regex_postprocessing
    title_filter = TitleFilter(regex_postprocessing=[""])
    assert title_filter.regex_postprocessing == []
    title_filter = TitleFilter(regex_postprocessing=["", "", ""])
    assert title_filter.regex_postprocessing == []

    # If a string is passed in, its converted to a list
    title_filter = TitleFilter(regex_postprocessing="Server \\d+: ")  # type: ignore[arg-type] # This is a test, it can load from config this way
    assert title_filter.regex_postprocessing == ["Server \\d+: "]
