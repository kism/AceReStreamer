"""CLI For Config generation."""

import argparse
import sys
from pathlib import Path

from pydantic import HttpUrl

from acere.core.config import (
    AceReStreamerConf,
    EPGInstanceConf,
    ScrapeSiteHTML,
    ScrapeSiteIPTV,
)
from acere.utils.logger import get_logger, setup_logger
from acere.version import __version__

logger = get_logger(__name__)


def _check_config_path(
    config_path: Path,
    extension: str,
    *,
    expect_config: bool = True,
    overwrite: bool = False,
) -> None:
    """Check if the config path is valid and has the correct extension."""
    cannot_proceed = False

    if expect_config and not config_path.is_file():
        logger.error("No configuration at: %s", config_path)
        cannot_proceed = True

    if overwrite:  # If we want to overwrite, we don't care if the file exists, break from this check
        pass
    elif (
        not expect_config  # If we don't expect a config, we continue this check
        and config_path.is_file()  # Fail if the file exists, since we are not expecting a config
    ):
        logger.error("Configuration file already exists at: %s", config_path)
        logger.error("Use --overwrite to overwrite the existing configuration file.")
        cannot_proceed = True

    if config_path.suffix != extension:
        logger.error(
            "Configuration file must have a %s extension, got %s",
            extension,
            config_path.suffix,
        )
        cannot_proceed = True

    if config_path.is_dir():
        logger.error("The specified path %s is a directory, not a file.", config_path)
        cannot_proceed = True

    if cannot_proceed:
        logger.error("Exiting due to configuration path issues.")
        sys.exit(1)


def generate_app_config_file(
    app_config_path: Path,
    *,
    overwrite: bool = False,
) -> None:
    """Generate a default configuration file at the specified path."""
    msg = (
        f"Overwriting existing configuration file at {app_config_path}"
        if overwrite
        else f"Generating configuration file at {app_config_path}"
    )
    _check_config_path(
        app_config_path, ".json", expect_config=False, overwrite=overwrite
    )

    logger.info(msg)

    config = AceReStreamerConf()
    if app_config_path.is_file():  # If we are here, we are overwriting
        try:
            logger.info("Loading existing configuration from %s", app_config_path)
            config = AceReStreamerConf.force_load_config_file(app_config_path)
        except Exception:  # noqa: BLE001 Naa, we are generating config
            logger.error("Failed to load existing configuration")  # noqa: TRY400 Short error for requests
            logger.info("Generating a new configuration file instead.")

    logger.info("Including HTML scraper in the configuration.")
    config.scraper.html.clear()
    config.scraper.html.append(
        ScrapeSiteHTML(name="Example HTML", url=HttpUrl("https://example.com"))
    )

    logger.info("Including IPTV M3U8 scraper in the configuration.")
    config.scraper.iptv_m3u8.clear()
    config.scraper.iptv_m3u8.append(
        ScrapeSiteIPTV(name="Example IPTV", url=HttpUrl("https://example.com/iptv.txt"))
    )

    config.epgs.clear()
    config.epgs.append(EPGInstanceConf())

    config.write_config(config_path=app_config_path)


def main() -> None:
    """Main CLI for config generation."""
    parser = argparse.ArgumentParser(
        description=f"Acestream Webplayer CLI {__version__} for generating config."
    )
    parser.add_argument(
        "--app-config",
        type=Path,
        default=None,
        help="Path to save the generated application configuration file.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing configuration files if they exist.",
        default=False,
    )
    args = parser.parse_args()

    setup_logger()

    if args.app_config is None:
        logger.error(
            "No application configuration path provided. Use --app-config to specify a path."
        )
        sys.exit(1)

    logger.info("Acestream Webplayer Config CLI %s", __version__)

    print()  # noqa: T201
    logger.info("--- Generating app configuration ---")
    generate_app_config_file(
        app_config_path=args.app_config,
        overwrite=args.overwrite,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
