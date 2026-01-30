"""CLI for scrape mode."""

import argparse
import sys
from pathlib import Path

import uvloop

from acere.core.config import AceReStreamerConf
from acere.instances.config import settings
from acere.utils.logger import get_logger, setup_logger
from acere.version import __version__

from .playlist import PlaylistCreator
from .readme import generate_readme
from .repo import generate_misc

logger = get_logger(__name__)


async def async_main() -> None:
    """Cli for adhoc scrape mode."""
    msg = f"Acestream Scrape CLI {__version__}"
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument(
        "--app-config",
        type=Path,
        default=None,
        help="Path to save the generated application configuration file.",
    )
    parser.add_argument(
        "-v",
        action="count",
        default=0,
        dest="verbose",
        help="Increase verbosity (can be used multiple times).",
    )
    args = parser.parse_args()

    if args.app_config is None:
        logger.error("No application configuration path provided. Use --app-config to specify a path.")
        sys.exit(1)

    if not args.app_config.is_file():
        logger.error("Application configuration file does not exist at: %s", args.app_config)
        sys.exit(1)

    # Here in CLI land, everything we touch will need the instance path to be set
    instance_path = args.app_config.parent

    setup_logger()

    logger.info(msg)
    cli_conf = AceReStreamerConf.force_load_config_file(config_path=args.app_config)
    cli_conf.write_config(config_path=args.app_config)
    settings.update_from(cli_conf)
    del cli_conf  # Ensure we don't use the old one

    pl_cr = PlaylistCreator(instance_path=instance_path)
    if len(settings.scraper.html) == 0 and len(settings.scraper.iptv_m3u8) == 0:
        logger.error("No scraper sites defined, cannot continue.")
        return

    if settings.scraper.tvg_logo_external_url is None:
        logger.error("No TVG logo external URL defined, cannot continue.")
        return

    settings.logging.setup_verbosity_cli(args.verbose)
    setup_logger(settings=settings.logging)

    logger.info("Starting scrape...")
    await pl_cr.scrape()

    logger.info("Generating README.md")

    generate_readme(
        instance_path=instance_path,
        external_base_url=settings.scraper.adhoc_playlist_external_url,
    )
    generate_misc(instance_path=instance_path)


def main() -> None:
    """Main entry point for scrape CLI."""
    uvloop.run(async_main())


if __name__ == "__main__":
    main()
