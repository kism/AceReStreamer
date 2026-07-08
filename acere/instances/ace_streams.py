from acere.database.handlers.acestreams import AceStreamDBHandler
from acere.instances import GlobalInstance

_ace_streams_handler = GlobalInstance("AceStreamDBHandler", factory=AceStreamDBHandler)
get_ace_streams_db_handler = _ace_streams_handler.get
