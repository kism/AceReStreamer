from acere.instances.config import settings
from acere.services.epg import EPGHandler

_epg_handler: EPGHandler | None = None


def get_epg_handler() -> EPGHandler:
    """Get the global AceStreamsDBHandler instance."""
    if _epg_handler is None:
        msg = "EPGHandler instance is not set."
        raise ValueError(msg)

    return _epg_handler


def set_epg_handler(handler: EPGHandler) -> None:
    """Set the global EPGHandler instance."""
    global _epg_handler  # noqa: PLW0603
    _epg_handler = handler
    _epg_handler.update_epgs(settings.epgs)
