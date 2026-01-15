"""Generic helper functions for AceReStreamer."""

import re

from acere.utils.logger import get_logger

logger = get_logger(__name__)

ACE_ID_LENGTH = 40

# Compiled regex
_NON_ALPHANUMERIC_PATTERN = re.compile(r"[^a-zA-Z0-9-]")
_DOUBLE_SPACE_PATTERN = re.compile(r"\s{2,}")
_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]+$")


def slugify(slug_input: str | bytes | None) -> str:
    """Convert a string to a slug."""
    if slug_input is None:
        return ""

    if isinstance(slug_input, bytes):
        slug_input = slug_input.decode()

    # Replace + with 'plus'
    slug_input = slug_input.replace("+", "plus")

    # Generate Slug, everything that isn't alphanumeric is now a space, which will become a hyphen later
    slug_input = _NON_ALPHANUMERIC_PATTERN.sub(" ", slug_input)

    # Remove excess spaces
    slug_input = _DOUBLE_SPACE_PATTERN.sub(" ", slug_input)

    # Remove prefix and suffix whitespace, replace anything left as a hyphen
    return slug_input.strip().replace(" ", "-").lower()


def check_valid_content_id_or_infohash(content_id: str) -> bool:
    """Check if the AceStream content_id or infohash is valid."""
    if len(content_id) != ACE_ID_LENGTH:
        return False

    if not _HEX_PATTERN.match(content_id):  # noqa: SIM103 eh
        return False

    return True
