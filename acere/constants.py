"""Constants used through the app."""

import os
from datetime import UTC, datetime
from pathlib import Path

import pytz

# Directories
## Directories Instance
_env_instance_dir = os.getenv("INSTANCE_DIR")
INSTANCE_DIR = Path(_env_instance_dir) if _env_instance_dir else Path(__file__).parent.parent / "instance"

DATABASE_FILE = INSTANCE_DIR / "acerestreamer.db"
SETTINGS_FILE = INSTANCE_DIR / "config.json"
TVG_LOGOS_DIR = INSTANCE_DIR / "tvg_logos"
EPG_XML_DIR = INSTANCE_DIR / "epg"

## Directories Internal
DEV_FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
DEV_BACKEND_DIR = Path(__file__).parent
DIST_DIR = DEV_BACKEND_DIR / "dist"  # Built frontend
STATIC_DIR = DIST_DIR / "static"  # Static that applies to the API/IPTV backend

# Timezone
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


# API
API_V1_STR = "/api/v1"
# Config
ENV_PREFIX = "ACERE_"


# EPG Related but used everywhere
SUPPORTED_TVG_LOGO_EXTENSIONS = ["png", "jpg", "jpeg", "webp", "svg"]
