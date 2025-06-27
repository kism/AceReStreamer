"""Constancts for AceReStreamer."""

from datetime import datetime
from pathlib import Path

OUR_TIMEZONE = datetime.now().astimezone().tzinfo
ACESTREAM_API_TIMEOUT = 3

# Lol
STATIC_DIRECTORY = Path(__file__).parent.parent / "static"
TEMPLATES_DIRECTORY = Path(__file__).parent.parent / "templates"
