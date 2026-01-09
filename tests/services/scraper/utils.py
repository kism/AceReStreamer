def common_title_check(title: str) -> None:
    """Common checks for titles in tests."""
    assert "000000000000" not in title, f"Placeholder title found: {title}"
    assert len(title) != 40, "Title should not the the content_id"
