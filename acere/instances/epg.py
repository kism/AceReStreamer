from acere.instances import GlobalInstance
from acere.instances.config import settings
from acere.services.epg import EPGHandler

_epg_handler: GlobalInstance[EPGHandler] = GlobalInstance("EPGHandler")
get_epg_handler = _epg_handler.get


def set_epg_handler(handler: EPGHandler) -> None:
    """Set the global EPGHandler instance."""
    _epg_handler.set(handler)
    handler.update_epgs(settings.epgs)
