"""Generic name processing functions shared between ace and iptv scrapers."""

import re

from acere.constants import SUPPORTED_TVG_LOGO_EXTENSIONS
from acere.instances.config import settings
from acere.instances.paths import get_app_path_handler
from acere.utils.helpers import slugify
from acere.utils.logger import get_logger

logger = get_logger(__name__)

STREAM_TITLE_MAX_LENGTH = 50

# Compiled regex patterns
COUNTRY_CODE_PATTERN = re.compile(r"\[([A-Z]{2})\]")

COMPILED_REGEX_CACHE: dict[str, re.Pattern[str]] = {}

# These should extract and remove the country code from the title
BAD_COUNTRY_CODE_FORMATS: list[re.Pattern[str]] = [
    re.compile(r"^[A-Z]{2}\s*[\|:-]\s*"),  # Starts with XX |
    re.compile(r"^[A-Z]{2}\s*▎\s*"),  # Starts with XX ▎
    re.compile(r"\([A-Z]{2}\)$"),  # Ends with (XX)
]


_COUNTRY_CODE_RE = re.compile(r"[A-Z]{2}")


def _normalize_country_code_format(title: str) -> str:
    """Reformat a country code from a bad format to [XX] appended at the end.

    Checks BAD_COUNTRY_CODE_FORMATS patterns in order. On the first match,
    removes the bad-format code and appends it as [XX].
    """
    for pattern in BAD_COUNTRY_CODE_FORMATS:
        match = pattern.search(title)
        if match:
            cc_match = _COUNTRY_CODE_RE.search(match.group(0))
            if cc_match:
                title = pattern.sub("", title).strip()
                return f"{title} [{cc_match.group(0)}]"
    return title


def _apply_regex_list(title: str, regex_list: list[str]) -> str:
    """Apply a list of regexes to a title, appending any extracted country code in [XX] format."""
    wip_title = title
    extracted_country_code: str | None = None

    for regex_str in regex_list:
        if regex_str not in COMPILED_REGEX_CACHE:
            COMPILED_REGEX_CACHE[regex_str] = re.compile(regex_str)

        compiled_regex = COMPILED_REGEX_CACHE[regex_str]
        match = compiled_regex.search(wip_title)
        if match:
            if extracted_country_code is None:
                cc_match = _COUNTRY_CODE_RE.search(match.group(0))
                if cc_match:
                    extracted_country_code = cc_match.group(0)
            wip_title = compiled_regex.sub("", wip_title).strip()

    if extracted_country_code:
        wip_title = f"{wip_title} [{extracted_country_code}]"

    return wip_title


def title_regex_cleanup(title: str, regex_list: list[str]) -> str:
    """Clean up a single title: normalize country codes then apply config regexes.

    Always normalizes bad country code formats (e.g. ``UK:`` → ``[UK]``).
    Then applies *regex_list* (from config) if non-empty.
    """
    title = _normalize_country_code_format(title)
    if regex_list:
        title = _apply_regex_list(title, regex_list)
    return title


def candidates_regex_cleanup(candidate_titles: list[str], regex_list: list[str]) -> list[str]:
    """Clean up a list of title candidates via title_regex_cleanup.

    Titles that become empty or contain only non-alphanumeric characters are dropped.
    """
    new_candidate_titles = []

    for title in candidate_titles:
        wip_title = title_regex_cleanup(title, regex_list)

        # If name is not empty or only non-alphanumeric characters, add it
        if wip_title and not all(not c.isalnum() for c in wip_title):
            new_candidate_titles.append(wip_title)
            if wip_title != title:
                logger.trace("Regex cleaned up title from '%s' to '%s'", title, wip_title)

    return new_candidate_titles


def trim_title(title: str) -> str:
    """Trim the title to a maximum length, only really needs to be used for HTML titles."""
    return title[:STREAM_TITLE_MAX_LENGTH].strip() if len(title) > STREAM_TITLE_MAX_LENGTH else title.strip()


def find_tvg_logo_image(title: str) -> str:
    """Find the TVG logo image for a given title."""
    tvg_logos_dir = get_app_path_handler().tvg_logos_dir
    title_slug = slugify(title)

    for extension in SUPPORTED_TVG_LOGO_EXTENSIONS:
        logo_path = tvg_logos_dir / f"{title_slug}.{extension}"
        if logo_path.is_file():
            return f"{title_slug}.{extension}"

    logger.warning("TVG logo not found, download manually and name it: %s.png", title_slug)

    return ""


def get_tvg_id_from_title(title: str) -> str:
    """Extract the TVG ID from the title, gets it into approximately epgshare01 format."""
    country_code_match = COUNTRY_CODE_PATTERN.search(title)
    if country_code_match:
        country_code = country_code_match.group(1)
        title_no_cc = title.replace(f"[{country_code}]", "").replace(" ", ".").strip()
        return f"{title_no_cc}.{country_code.lower()}".replace("..", ".").strip(".")

    return ""


def populate_group_title(group_title: str, title: str) -> str:
    """Cleanup the group title."""
    # Put into sentence case
    for category, keywords in settings.ace.scraper.category_mapping.items():
        # For example, if the catetory is Sports but the group title is sport
        if any(keyword in group_title.lower() for keyword in keywords):
            group_title = category
            break

        # For example, if no group title, but the title contains football etc
        if any(keyword in title.lower() for keyword in keywords):
            group_title = category
            break

    group_title = group_title.strip().capitalize()

    return group_title or "General"
