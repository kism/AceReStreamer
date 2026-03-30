from typing import Any

from acere.utils.logger import get_logger

logger = get_logger(__name__)


# region Migration
def _migrate_config_data(data: dict[str, Any]) -> dict[str, Any]:
    """Migrate old config format...

    - top-level 'app' and 'scraper' keys into 'ace'
    - REMOTE_SETTINGS_URL to remote_settings.
    """
    if "app" in data and "ace" not in data:
        logger.warning("Migrating old config format: 'app' and 'scraper' -> 'ace'")
        ace = dict(data.pop("app", {}))
        ace["scraper"] = data.pop("scraper", {})
        data["ace"] = ace

    # Migrate REMOTE_SETTINGS_URL to remote_settings
    if "REMOTE_SETTINGS_URL" in data and "remote_settings" not in data:
        logger.warning("Migrating old config format: 'REMOTE_SETTINGS_URL' -> 'remote_settings.url'")
        remote_url = data.pop("REMOTE_SETTINGS_URL", None)
        if remote_url:
            data["remote_settings"] = {"url": remote_url, "enable_epg": True, "enable_ace": True}

    return data
