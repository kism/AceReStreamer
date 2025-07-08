"""Constancts for AceReStreamer."""

from datetime import UTC, datetime
from pathlib import Path

import pytz

OUR_TIMEZONE = datetime.now().astimezone().tzinfo or UTC
OUR_TIMEZONE_NAME = str(OUR_TIMEZONE)

_current_time = datetime.now(tz=OUR_TIMEZONE)

for tz in pytz.all_timezones:  # Iterate through all timzones list[str]
    timezone = pytz.timezone(tz)  # Create a timezone object based on the string
    # Using the timezone object, get the name of the timezone from datetime
    tz_name = _current_time.astimezone(timezone).tzname()
    if tz_name == OUR_TIMEZONE_NAME:
        OUR_TIMEZONE_NAME = tz
        break


# Lol
STATIC_DIRECTORY = Path(__file__).parent.parent / "static"
TEMPLATES_DIRECTORY = Path(__file__).parent.parent / "templates"

SUPPORTED_TVG_LOGO_EXTENSIONS = ["png", "jpg", "jpeg", "webp", "svg"]
