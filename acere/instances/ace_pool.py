from typing import TYPE_CHECKING

from acere.instances import GlobalInstance

if TYPE_CHECKING:
    from acere.services.ace_pool.pool import AcePool
else:
    AcePool = object

_ace_pool: GlobalInstance[AcePool] = GlobalInstance("AcePool")
set_ace_pool = _ace_pool.set
get_ace_pool = _ace_pool.get
