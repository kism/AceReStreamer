"""Helper functions for scrapers."""

import re
from pathlib import Path

from .config import TitleFilter
from .logger import get_logger
from .scraper_objects import FlatFoundAceStream

logger = get_logger(__name__)

STREAM_TITLE_MAX_LENGTH = 50
ACE_ID_LENGTH = 40
ACE_URL_PREFIXES = ["http://127.0.0.1:6878/ace/getstream?id=", "acestream://"]


class M3UNameReplacer:
    """Cache for M3U text replacements."""

    def __init__(self, instance_path: Path | None = None) -> None:
        """Initialize the cache."""
        self.cache: dict[str, str] = {}
        self.instance_path = instance_path
        if instance_path:
            self._load_cache()

    def do_replacements(self, name: str) -> str:
        """Perform replacements in the M3U content."""
        if not self.instance_path:
            logger.warning("No instance path set, cannot perform M3U replacements.")
            return name

        if self.cache == {}:
            self._load_cache()

        for key, value in self.cache.items():
            if key in name:
                logger.debug("Replacing '%s' with '%s' in '%s'", key, value, name)
                name = name.replace(key, value)

        return name

    def _load_cache(self) -> None:
        """Load M3U replacements from the instance path."""
        if not self.instance_path:
            logger.warning("No instance path set, cannot perform M3U replacements.")
            return

        desired_cell_count = 2  # CSV is just my key,value pairs

        m3u_path = self.instance_path / "m3u_replacements.csv"
        if m3u_path.exists():
            with m3u_path.open("r", encoding="utf-8") as file:
                for line in file:
                    line_tmp = line.strip()
                    if not line_tmp or line_tmp.startswith("#"):
                        continue
                    parts = line_tmp.split(",")
                    if len(parts) == desired_cell_count:
                        self.cache[parts[0].strip()] = parts[1].strip()
        else:
            m3u_path.touch()


m3u_replacer = M3UNameReplacer()


def start_m3u_replacer(instance_path: str) -> None:
    """Start the M3U replacer with the instance path."""
    global m3u_replacer  # noqa: PLW0603 aaaaa
    m3u_replacer = M3UNameReplacer(Path(instance_path))


def cleanup_candidate_title(title: str) -> str:
    """Cleanup the candidate title."""
    title = title.strip()

    for prefix in ACE_URL_PREFIXES:
        title = title.removeprefix(prefix)

    title = title.split("\n")[0].strip()  # Remove any newlines
    title = re.sub(r"\b[0-9a-fA-F]{40}\b", "", title).strip() # Remove any ace 40 digit hex ids from the title
    title = m3u_replacer.do_replacements(title)
    return title.strip()



def candidates_regex_cleanup(candidate_titles: list[str], regex: str) -> list[str]:
    """Cleanup the title using a regex."""
    if regex == "":
        return candidate_titles

    new_candidate_titles = []

    for title in candidate_titles:
        title_new = re.sub(regex, "", title).strip()
        if title_new != "":
            new_candidate_titles.append(title_new)

    return new_candidate_titles


def get_streams_as_iptv(streams: list[FlatFoundAceStream], hls_path: str) -> str:
    """Get the found streams as an IPTV M3U8 string."""
    m3u8_content = "#EXTM3U\n"

    for stream in streams:
        logger.debug(stream)
        if stream.quality > 0:
            # Country codes are 2 characters between square brackets, e.g. [US]
            country_code_regex = re.search(r"\[([A-Z]{2})\]", stream.title)
            tvg_id = 'tvg-id=""'

            if country_code_regex and isinstance(country_code_regex.group(1), str):
                country_code = country_code_regex.group(1)
                stream_title_no_cc = stream.title.replace(f"[{country_code}]", "").strip()
                tvg_id = f'tvg-id="{stream_title_no_cc}.{country_code.lower()}"'

            m3u8_content += f"#EXTINF:-1 {tvg_id},{stream.title}\n"
            m3u8_content += f"{hls_path}{stream.ace_id}\n"

    return m3u8_content


def check_valid_ace_id(ace_id: str) -> bool:
    """Check if the AceStream ID is valid."""
    if len(ace_id) != ACE_ID_LENGTH:
        logger.warning("AceStream ID is not the expected length (%d), skipping: %s", ACE_ID_LENGTH, ace_id)
        return False

    if not re.match(r"^[0-9a-fA-F]+$", ace_id):
        logger.warning("AceStream ID contains invalid characters: %s", ace_id)
        return False

    return True


def extract_ace_id_from_url(url: str) -> str:
    """Extract the AceStream ID from a URL."""
    url = url.strip()
    for prefix in ACE_URL_PREFIXES:
        url = url.replace(prefix, "")

    if "&" in url:
        url = url.split("&")[0]

    return url


def check_valid_ace_url(url: str) -> bool:
    """Check if the AceStream URL is valid."""
    return any(url.startswith(prefix) for prefix in ACE_URL_PREFIXES)


def check_title_allowed(title: str, title_filter: TitleFilter) -> bool:
    """Check if the title contains any disallowed words."""
    if not title:
        return False

    title = title.lower()

    if any(word.lower() in title for word in title_filter.always_exclude_words):
        logger.trace("Title '%s' is not allowed, skipping", title)
        return False

    if any(word.lower() in title for word in title_filter.always_include_words):
        return True

    if any(word.lower() in title for word in title_filter.exclude_words):
        logger.trace("Title '%s' is not allowed, skipping", title)
        return False

    if title_filter.include_words:
        return any(word.lower() in title for word in title_filter.include_words)

    return True
