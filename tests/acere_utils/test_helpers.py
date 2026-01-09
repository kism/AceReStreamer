from acere.utils.helpers import check_valid_content_id_or_infohash, slugify


def test_slugify() -> None:
    assert slugify("This is a Test!") == "this-is-a-test"
    assert slugify(b"Another_Test@123") == "another-test-123"
    assert slugify("  Multiple   Spaces  ") == "multiple-spaces"
    assert slugify("Special$$$Characters%%%") == "special-characters"


def test_check_valid_content_id_or_infohash() -> None:
    # Valid hashes are 40 hexadecimal characters
    valid_id = "a" * 40
    invalid_id_length = "a" * 39
    invalid_id_chars = "g" * 40

    assert check_valid_content_id_or_infohash(valid_id) is True
    assert check_valid_content_id_or_infohash(invalid_id_length) is False
    assert check_valid_content_id_or_infohash(invalid_id_chars) is False
