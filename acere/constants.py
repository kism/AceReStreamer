"""Constants used through the app."""

import os
from pathlib import Path

# Directories
## Directories Instance
_env_instance_dir = os.getenv("INSTANCE_DIR")
DEFAULT_INSTANCE_PATH = Path(_env_instance_dir) if _env_instance_dir else Path(__file__).parent.parent / "instance"

## Directories Internal
DEV_BACKEND_DIR = Path(__file__).parent
DIST_DIR = DEV_BACKEND_DIR / "dist"  # Built frontend
STATIC_DIR = DIST_DIR / "static"  # Static that applies to the API/IPTV backend

# API
API_V1_STR = "/api/v1"
# Config
ENV_PREFIX = "ACERE_"


# EPG Related but used everywhere
SUPPORTED_TVG_LOGO_EXTENSIONS = ["png", "jpg", "jpeg", "webp", "svg"]


XC_USER_AGENT = "TiviMate/5.1.6 (Android 12)"
