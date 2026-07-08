from acere.database.handlers.category_xc import CategoryXCCategoryIDDatabaseHandler
from acere.instances import GlobalInstance

_xc_category_handler = GlobalInstance(
    "CategoryXCCategoryIDDatabaseHandler",
    factory=CategoryXCCategoryIDDatabaseHandler,
)
get_xc_category_db_handler = _xc_category_handler.get
