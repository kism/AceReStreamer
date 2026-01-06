"""Database Handlers."""

from .category_xc import CategoryXCCategoryIDDatabaseHandler
from .content_id_infohash import ContentIdInfohashDatabaseHandler
from .content_id_xc_id import ContentIdXCIDDatabaseHandler
from .quality_cache import AceQualityCacheHandler

__all__ = [
    "AceQualityCacheHandler",
    "BaseDatabaseHandler",
    "CategoryXCCategoryIDDatabaseHandler",
    "ContentIdInfohashDatabaseHandler",
    "ContentIdXCIDDatabaseHandler",
]
