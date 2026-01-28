from acere.instances.config import settings
from acere.services.epg import EPGHandler

_epg_handler: EPGHandler | None = None


def get_epg_handler() -> EPGHandler:
    """Get the global AceStreamsDBHandler instance."""
    global _epg_handler  # noqa: PLW0603
    if _epg_handler is None:
        _epg_handler = EPGHandler()
        _epg_handler.load_config(settings.epgs)

    return _epg_handler
