"""Module for handling Electronic Program Guide (EPG) data."""

from pathlib import Path

from .config import EPGInstanceConf
from .logger import get_logger

logger = get_logger(__name__)


class EPG:
    """An Electronic Program Guide (EPG) entry."""

    def __init__(self, epg_conf: EPGInstanceConf) -> None:
        """Initialize the EPG entry with a URL."""
        self.url = epg_conf.url
        self.format = epg_conf.format
        self.region_code = epg_conf.region_code


class EPGHandler:
    """Handler for EPG (Electronic Program Guide) data."""

    def __init__(self, epg_conf_list: list[EPGInstanceConf], instance_path: Path | None = None) -> None:
        """Initialize the EPGHandler with a list of URLs."""
        self.epgs: list[EPG] = []

        for epg_conf in epg_conf_list:
            self.epgs.append(EPG(epg_conf=epg_conf))

        logger.info(instance_path)
