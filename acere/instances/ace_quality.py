"""Global instance for the quality cache handler."""

from acere.database.handlers.quality_cache import AceQualityCacheHandler
from acere.instances import GlobalInstance

_quality_handler: GlobalInstance[AceQualityCacheHandler] = GlobalInstance("AceQualityCacheHandler")
set_quality_handler = _quality_handler.set
get_quality_handler = _quality_handler.get
