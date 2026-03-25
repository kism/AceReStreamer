"""CLI to run the IPTV proxy scrape process and print found streams."""

import argparse
import asyncio
import sys
from pathlib import Path

import uvloop
from rich.table import Table

from acere.config import AceReStreamerConf
from acere.instances.config import settings
from acere.instances.paths import setup_app_path_handler
from acere.services.scraper.iptv import IPTVProxyScraper
from acere.services.scraper.models import FoundIPTVStream
from acere.utils.cli import console
from acere.utils.logger import setup_logger


async def async_main() -> None:
    """Run the IPTV proxy scrape and print results."""
    parser = argparse.ArgumentParser(description="Run the IPTV proxy scrape process and print found streams.")
    parser.add_argument(
        "--app-config",
        type=Path,
        default=None,
        required=True,
        help="Path to the application configuration file.",
    )
    parser.add_argument(
        "-v",
        action="count",
        default=0,
        dest="verbose",
        help="Increase verbosity (can be used multiple times).",
    )
    args = parser.parse_args()

    settings.logging.setup_verbosity_cli(args.verbose)
    setup_logger(settings=settings.logging)

    if not args.app_config.is_file():
        console.print(f"[red]Configuration file does not exist at: {args.app_config}[/red]")
        sys.exit(1)

    setup_app_path_handler(instance_path=args.app_config.parent)

    cli_conf = AceReStreamerConf.force_load_config_file(config_path=args.app_config)
    settings.update_from(cli_conf)

    iptv_conf = settings.iptv
    if not iptv_conf.xtream and not iptv_conf.m3u8:
        console.print("[yellow]No IPTV proxy sources configured.[/yellow]")
        return

    scraper = IPTVProxyScraper()

    tasks = [scraper.scrape_m3u8_source(source) for source in iptv_conf.m3u8]
    tasks.extend(scraper.scrape_xtream_source(source) for source in iptv_conf.xtream)

    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    found_streams: list[FoundIPTVStream] = []
    for result in all_results:
        if isinstance(result, list):
            found_streams.extend(result)
        else:
            console.print(f"[red]Error scraping source: {result}[/red]")

    if not found_streams:
        console.print("[yellow]No streams found.[/yellow]")
        return

    table = Table(title=f"Found {len(found_streams)} IPTV Streams")
    table.add_column("Title", style="cyan")
    table.add_column("Source", style="green")
    table.add_column("Group", style="yellow")
    table.add_column("TVG ID", style="dim")
    table.add_column("Upstream URL", style="dim", no_wrap=True)

    for stream in found_streams:
        table.add_row(stream.title, stream.source_name, stream.group_title, stream.tvg_id, stream.upstream_url)

    console.print(table)


def main() -> None:
    """Main entry point for IPTV scraper CLI."""
    uvloop.run(async_main())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt, EOFError:
        console.print("\nExiting...")
