"""Constants used through the app."""

import os
from pathlib import Path

_env_instance_dir = os.getenv("INSTANCE_DIR")

INSTANCE_DIR = Path(_env_instance_dir) if _env_instance_dir else Path(__file__).parent.parent / "instance"

DEV_FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
DEV_BACKEND_DIR = Path(__file__).parent

DATABASE_FILE = INSTANCE_DIR / "acerestreamer.db"
SETTINGS_FILE = INSTANCE_DIR / "config.json"
TVG_LOGOS_DIR = INSTANCE_DIR / "tvg_logos"
DIST_DIR = DEV_BACKEND_DIR / "dist"  # Built frontend
STATIC_DIR = DIST_DIR / "static"  # Static that applies to the API/IPTV backend
API_V1_STR = "/api/v1"
ENV_PREFIX = "ACERE_"
