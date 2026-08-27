from acere.database.handlers.content_id_xc_id import ContentIdXcIdDatabaseHandler
from acere.instances import GlobalInstance

_xc_stream_handler = GlobalInstance("ContentIdXcIdDatabaseHandler", factory=ContentIdXcIdDatabaseHandler)
get_xc_stream_db_handler = _xc_stream_handler.get
