"""Generic helper functions for Ace ReStreamer."""

import re

from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)

ACE_ID_LENGTH = 40

# Compiled regex
_NON_ALPHANUMERIC_PATTERN = re.compile(r"[^a-zA-Z0-9-]")
_DOUBLE_SPACE_PATTERN = re.compile(r"\s{2,}")
_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]+$")


def slugify(file_name: str | bytes) -> str:
    """Convert a file name into a URL-safe slug format.

    Standardizes names by removing common podcast prefixes/suffixes and
    converting to hyphenated lowercase alphanumeric format.
    """
    if isinstance(file_name, bytes):
        file_name = file_name.decode()

    # Generate Slug, everything that isn't alphanumeric is now a space, which will become a hyphen later
    file_name = _NON_ALPHANUMERIC_PATTERN.sub(" ", file_name)

    # Remove excess spaces
    file_name = _DOUBLE_SPACE_PATTERN.sub(" ", file_name)

    # Remove prefix and suffix whitespace, replace anything left as a hyphen
    return file_name.strip().replace(" ", "-")


def check_valid_content_id_or_infohash(content_id: str) -> bool:
    """Check if the AceStream content_id or infohash is valid."""
    if len(content_id) != ACE_ID_LENGTH:
        return False

    if not _HEX_PATTERN.match(content_id):  # noqa: SIM103 eh
        return False

    return True


def log_unexpected_args(expected_args: list[str], received_args: list[str], endpoint: str) -> None:
    """Log unexpected query parameters."""
    unexpected_args = [arg for arg in received_args if arg not in expected_args]
    if unexpected_args:
        logger.warning(
            "Unexpected query parameters in %s: %s",
            endpoint,
            ", ".join(unexpected_args),
        )
