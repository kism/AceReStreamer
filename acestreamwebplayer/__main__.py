"""CLI For Adhoc Tasks."""

import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .config import AcestreamWebplayerConfig, ScrapeSiteHTML, ScrapeSiteIPTV
from .logger import LOG_LEVELS, _set_log_level

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

logger = logging.getLogger(__name__)


def generate_config_file(config_path: Path, *, include_html: bool = False, include_iptv: bool = False) -> None:
    """Generate a default configuration file at the specified path."""
    if config_path.exists():
        logger.error("Configuration file already exists at %s", config_path)
        sys.exit(1)

    if config_path.is_dir():
        logger.error("The specified path %s is a directory, not a file.", config_path)
        sys.exit(1)

    if config_path.suffix != ".toml":
        logger.error("Configuration file must have a .toml extension, got %s", config_path.suffix)
        sys.exit(1)

    logger.info("Generating default configuration file at %s", config_path)
    config = AcestreamWebplayerConfig()

    if include_html:
        logger.info("Including HTML scraper in the configuration.")
        config.app.ace_scrape_settings.site_list_html.append(ScrapeSiteHTML())

    if include_iptv:
        logger.info("Including IPTV M3U8 scraper in the configuration.")
        config.app.ace_scrape_settings.site_list_iptv_m3u8.append(ScrapeSiteIPTV())

    config.write_config(config_location=config_path)
    logger.info("Configuration file created successfully at %s", config_path)


def main() -> None:
    """Main CLI for adhoc tasks."""
    parser = argparse.ArgumentParser(description="Acestream Webplayer CLI for adhoc tasks.")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show the version of the Acestream Webplayer.",
    )
    parser.add_argument(
        "--generate-config",
        type=Path,
        default=None,
        required=False,
    )
    parser.add_argument(
        "--config-html-scraper",
        action="store_true",
        help="Include a scraper for HTML sites in the generated configuration.",
    )
    parser.add_argument(
        "--config-iptv-scraper",
        action="store_true",
        help="Include a scraper for IPTV M3U8 sites in the generated configuration.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=LOG_LEVELS,
        help="Set the logging level for the application.",
    )
    args = parser.parse_args()

    _set_log_level(logger, args.log_level)

    logger.info("Acestream Webplayer CLI %s started with log level: %s", __version__, args.log_level)

    if args.version:
        logger.info("Acestream Webplayer version %s", __version__)
        sys.exit(0)

    if args.generate_config:
        logger.info("Generating configuration file at %s", args.generate_config)
        generate_config_file(
            args.generate_config,
            include_html=args.config_html_scraper,
            include_iptv=args.config_iptv_scraper,
        )


if __name__ == "__main__":
    main()
