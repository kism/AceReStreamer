"""AceStream Manager instance."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from acere.services.ace.manager import AceManager
else:
    AceManager = object

_ace_manager: AceManager | None = None


def set_ace_manager(manager: AceManager) -> None:
    """Set the global AceManager instance."""
    global _ace_manager
    _ace_manager = manager
    _ace_manager.start_scrape_thread()


def get_ace_manager() -> AceManager:
    """Get the global AceManager instance."""
    if _ace_manager is None:
        msg = "AceManager instance is not set."
        raise ValueError(msg)
    return _ace_manager
