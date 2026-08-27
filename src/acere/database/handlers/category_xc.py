"""Handler for category xc category id."""

from sqlmodel import select

from acere.database.models import CategoryXCCategoryID
from acere.services.xc.models import XCCategory
from acere.utils.logger import get_logger

from .base import BaseDatabaseHandler

logger = get_logger(__name__)


class CategoryXCCategoryIDDatabaseHandler(BaseDatabaseHandler):
    """Handler for category XC category ID mapping."""

    def get_xc_category_id(self, category_name: str) -> int:
        """Get the XC category ID for a given category name."""
        with self._get_session() as session:
            result = session.exec(
                select(CategoryXCCategoryID).where(CategoryXCCategoryID.category == category_name)
            ).first()
            if result is None:
                result = CategoryXCCategoryID(category=category_name)
                session.add(result)
                session.commit()
                logger.trace(
                    "Created new XC category ID mapping: %s -> %d",
                    category_name,
                    result.xc_category_id,
                )
            if result.xc_category_id is None:  # Can't happen, the DB assigns the PK on insert
                msg = f"No xc_category_id assigned for category {category_name}"
                raise RuntimeError(msg)
            return result.xc_category_id

    def get_category_name(self, xc_category_id: int) -> str | None:
        """Get the category name for a given XC category ID."""
        with self._get_session() as session:
            result = session.exec(
                select(CategoryXCCategoryID).where(CategoryXCCategoryID.xc_category_id == xc_category_id)
            ).first()
            return result.category if result else None

    def get_all_categories_api(self, categories_in_use: set[int]) -> list[XCCategory]:
        """Get all categories as a list of XCCategory objects."""
        with self._get_session() as session:
            categories = session.exec(select(CategoryXCCategoryID)).all()
            return [
                XCCategory(category_id=str(cat.xc_category_id), category_name=cat.category)
                for cat in categories
                if cat.xc_category_id in categories_in_use
            ]
