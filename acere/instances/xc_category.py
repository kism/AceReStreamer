from acere.database.handlers.category_xc import CategoryXCCategoryIDDatabaseHandler

_xc_category_handler: CategoryXCCategoryIDDatabaseHandler | None = None


def get_xc_category_db_handler() -> CategoryXCCategoryIDDatabaseHandler:
    """Get the global AceStreamsDBHandler instance."""
    global _xc_category_handler  # noqa: PLW0603
    if _xc_category_handler is None:
        _xc_category_handler = CategoryXCCategoryIDDatabaseHandler()
    return _xc_category_handler
