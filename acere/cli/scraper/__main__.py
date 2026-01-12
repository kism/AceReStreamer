"""CLI for scrape mode."""

import argparse
import asyncio
import sys
from pathlib import Path

import uvloop

from acere.core.config import AceReStreamerConf
from acere.utils.logger import get_logger, setup_logger
from acere.version import __version__

from .playlist import PlaylistCreator
from .readme import generate_readme
from .repo import generate_misc

logger = get_logger(__name__)

uvloop.install()


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
        help="Increase verbosity (can be used multiple times).",
    )
    args = parser.parse_args()

    if args.app_config is None:
        logger.error("No application configuration path provided. Use --app-config to specify a path.")
        sys.exit(1)

    instance_path = args.app_config.parent

    setup_logger()

    logger.info(msg)
    conf = AceReStreamerConf.force_load_config_file(config_path=args.app_config)
    conf.write_config(config_path=args.app_config)
    pl_cr = PlaylistCreator(instance_path=instance_path, config=conf)
    if len(conf.scraper.html) == 0 and len(conf.scraper.iptv_m3u8) == 0:
        logger.error("No scraper sites defined, cannot continue.")
        return

    if conf.scraper.tvg_logo_external_url is None:
        logger.error("No TVG logo external URL defined, cannot continue.")
        return

    conf.logging.setup_verbosity_cli(args.v)

    setup_logger(settings=conf.logging)

    logger.info("Starting scrape...")
    await pl_cr.scrape()

    logger.info("Generating README.md")

    generate_readme(
        instance_path=instance_path,
        external_base_url=conf.scraper.adhoc_playlist_external_url,
    )
    generate_misc(instance_path=instance_path)


def main() -> None:
    """Main entry point for scrape CLI."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
