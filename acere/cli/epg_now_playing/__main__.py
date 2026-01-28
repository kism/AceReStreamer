import argparse
from pathlib import Path

from lxml import etree
from pydantic import HttpUrl

from acere.constants import EPG_XML_DIR as DEFAULT_EPG_XML_DIR
from acere.core.config import EPGInstanceConf
from acere.services.epg.epg import EPG
from acere.services.epg.helpers import find_current_program_xml, normalise_epg_tvg_id
from acere.utils.cli import console, prompt


def find_now_playing(tvg_id: str, epgs: dict[str, EPG]) -> None:
    matches: list[str] = []

    tvg_id_new = normalise_epg_tvg_id(tvg_id)

    if tvg_id_new != tvg_id:
        # This will happen in the EPGs anyway
        console.print(f"[yellow]Normalized tvg_id '{tvg_id}' to '{tvg_id_new}'[/yellow]")

    tvg_id = tvg_id_new or tvg_id

    for epg_name, epg in epgs.items():
        epg_root = epg.get_epg_etree_normalised()
        if epg_root is None:
            continue

        title, description = find_current_program_xml(tvg_id, epg_root)
        if title or description:
            matches.append(f"{epg_name}: {title or '<No Title>'} - {description or '<No Description>'}")

    if matches:
        console.print(f"Now playing for tvg_id '{tvg_id}':")
        for match in matches:
            console.print(f"  {match}")
    else:
        console.print(f"[yellow]No current program found for tvg_id '{tvg_id}'[/yellow]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Tool to check what every epg thinks is playing for a given tvg_id")
    parser.add_argument(
        "--dir",
        "--epg-dir",
        type=Path,
        default=DEFAULT_EPG_XML_DIR,
        help="Path to the EPG XML directory",
    )
    parser.add_argument("--tvg-id", type=str, default=None)
    args = parser.parse_args()

    epg_dir = args.dir
    if not epg_dir.is_dir():
        console.print(f"[red]EPG directory not found at: {epg_dir}[/red]")
        return

    epgs: dict[str, EPG] = {}
    for epg_file in epg_dir.glob("*.xml"):
        try:
            epg = EPG(EPGInstanceConf(url=HttpUrl(f"file://{epg_file.resolve()}")))
            epg.saved_file_path = epg_file
            epgs[epg_file.name] = epg
        except etree.XMLSyntaxError as e:
            if epg_file.stat().st_size == 0:
                console.print(f"[yellow]Removing empty epg xml file: {epg_file.name}[/yellow]")
                epg_file.unlink()
            else:
                console.print(f"[red]Failed to parse EPG file {epg_file.name}: {e}[/red]")

    console.print(f"Found {len(epgs)} EPG files in {epg_dir}\n")

    if args.tvg_id:
        find_now_playing(args.tvg_id, epgs)
        return

    user_input = ""
    while True:
        console.print()
        user_input = prompt("Enter a tvg_id to check now playing (or 'exit' to quit)")
        if user_input.lower() in ("exit", "quit"):
            break

        find_now_playing(user_input, epgs)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        console.print("\nExiting...")
