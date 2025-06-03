"""Demo object."""

from .config import AppConfDef
from .logger import get_logger

logger = get_logger(__name__)


# KISM-BOILERPLATE: Demo object, doesn't do much
class MyCoolObject:
    """Demo object."""

    def __init__(self, aw_conf: AppConfDef) -> None:
        """Init MyCoolObject."""
        logger.debug("Creating MyCoolObject")
        logger.debug(aw_conf)
