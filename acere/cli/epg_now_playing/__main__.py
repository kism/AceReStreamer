import argparse

from pathlib import Path

from acere.utils.cli import console, prompt

from acere.constants import DATABASE_FILE, EPG_XML_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="EPG Now Playing CLI Tool")
    parser.add_argument(
        "--epg-dir",
        type=Path,
        default=EPG_XML_DIR,
        help="Path to the EPG XML directory",
    )
    args = parser.parse_args()


if __name__ == "__main__":
    main()
