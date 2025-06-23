"""Generic helper functions for Ace ReStreamer."""

import re

from .logger import get_logger

logger = get_logger(__name__)

ACE_ID_LENGTH = 40


def slugify(file_name: str | bytes) -> str:
    """Convert a file name into a URL-safe slug format.

    Standardizes names by removing common podcast prefixes/suffixes and
    converting to hyphenated lowercase alphanumeric format.
    """
    if isinstance(file_name, bytes):
        file_name = file_name.decode()

    # Generate Slug, everything that isn't alphanumeric is now a space, which will become a hyphen later
    file_name = re.sub(r"[^a-zA-Z0-9-]", " ", file_name)

    # Remove excess spaces
    while "  " in file_name:
        file_name = file_name.replace("  ", " ")

    # Remove prefix and suffix whitespace, replace anything left as a hyphen
    return file_name.strip().replace(" ", "-")


def check_valid_ace_id(ace_id: str) -> bool:
    """Check if the AceStream ID is valid."""
    if len(ace_id) != ACE_ID_LENGTH:
        logger.warning(
            "AceStream ID is not the expected length %d != %d , skipping: %s", ACE_ID_LENGTH, len(ace_id), ace_id
        )
        return False

    if not re.match(r"^[0-9a-fA-F]+$", ace_id):
        logger.warning("AceStream ID contains invalid characters: %s", ace_id)
        return False

    return True
