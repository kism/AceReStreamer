"""Generic helper functions for Ace ReStreamer."""

import re


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
