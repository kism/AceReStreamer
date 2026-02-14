"""TVG logo downloading utilities for IPTV scrapers."""

from pathlib import Path

import aiohttp
from pydantic import HttpUrl

from acere.constants import SUPPORTED_TVG_LOGO_EXTENSIONS
from acere.instances.config import settings
from acere.instances.paths import get_app_path_handler
from acere.utils.helpers import slugify
from acere.utils.logger import get_logger

logger = get_logger(__name__)


async def fetch_logo_content(logo_url: HttpUrl, title: str) -> bytes | None:
    """Download logo content from a URL.

    Args:
        logo_url: URL to download the logo from
        title: Stream title (for logging)

    Returns:
        Logo content as bytes, or None if download failed or content is invalid
    """
    output_logo = None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                logo_url.encoded_string(), timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                response.raise_for_status()
                output_logo = await response.read()
    except (aiohttp.ClientError, TimeoutError) as e:
        error_short = type(e).__name__
        logger.debug("Error downloading TVG logo for %s [%s], %s", title, logo_url, error_short)

    if "git-lfs" in (output_logo or b"").decode(errors="ignore"):
        logger.warning("TVG logo for %s appears to be a Git LFS placeholder, skipping", title)
        return None

    return output_logo


def get_logo_path_for_title(title: str, extension: str | None = None) -> Path:
    """Get the filesystem path for a logo given a stream title.

    Args:
        title: Stream title
        extension: File extension (without dot), or None to just get the base path

    Returns:
        Path where the logo should be saved
    """
    tvg_logos_path = get_app_path_handler().tvg_logos_dir
    title_slug = slugify(title)

    if extension:
        return tvg_logos_path / f"{title_slug}.{extension}"
    return tvg_logos_path / title_slug


async def download_and_save_logo(logo_url: HttpUrl | None, title: str) -> None:
    """Download and save a TVG logo for a stream.

    This function:
    1. Checks if logo already exists (skips if found)
    2. Tries external URL source if configured in settings
    3. Falls back to provided URL
    4. Validates file extension
    5. Downloads and saves to disk

    Args:
        logo_url: The TVG logo URL to download from (can be None)
        title: Stream title
    """
    # Check if logo already exists
    for extension in SUPPORTED_TVG_LOGO_EXTENSIONS:
        logo_path = get_logo_path_for_title(title, extension)
        if logo_path.is_file():
            return

    # Try external URL source if configured
    if settings.scraper.tvg_logo_external_url is not None:
        title_slug = slugify(title)
        for extension in SUPPORTED_TVG_LOGO_EXTENSIONS:
            file_name = f"{title_slug}.{extension}"
            external_url = HttpUrl(f"{settings.scraper.tvg_logo_external_url}/{file_name}")

            logo_content = await fetch_logo_content(external_url, title)
            if logo_content is not None:
                logo_path = get_logo_path_for_title(title, extension)
                logo_path.parent.mkdir(parents=True, exist_ok=True)
                with logo_path.open("wb") as file:
                    file.write(logo_content)
                return

    # Fall back to provided URL
    if logo_url is None:
        logger.debug("No TVG logo URL found for %s", title)
        return

    # Validate file extension
    url_file_extension = logo_url.encoded_string().split(".")[-1]
    url_file_extension = url_file_extension.split("?")[0]
    if url_file_extension.lower() not in SUPPORTED_TVG_LOGO_EXTENSIONS:
        logger.warning(
            "Unsupported TVG logo file extension for %s: %s",
            title,
            url_file_extension,
        )
        return

    # Download and save
    logger.info("Downloading TVG logo for %s from m3u8 %s", title, logo_url)
    content = await fetch_logo_content(logo_url, title)
    if content is None:
        return

    logo_path = get_logo_path_for_title(title, url_file_extension)
    logo_path.parent.mkdir(parents=True, exist_ok=True)
    with logo_path.open("wb") as file:
        file.write(content)
