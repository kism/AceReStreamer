from typing import TYPE_CHECKING

import pytest
from sqlmodel import create_engine

from acere.database.handlers.category_xc import CategoryXCCategoryIDDatabaseHandler

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object


@pytest.fixture
def handler(tmp_path: Path) -> CategoryXCCategoryIDDatabaseHandler:
    """Fixture for CategoryXCCategoryIDDatabaseHandler."""
    test_engine = create_engine(f"sqlite:///{tmp_path / 'test_category_xc.db'}", echo=False)
    return CategoryXCCategoryIDDatabaseHandler(test_engine=test_engine)


def test_get_xc_category_id_is_stable(handler: CategoryXCCategoryIDDatabaseHandler) -> None:
    """Same category name always returns same xc_category_id."""
    id_1 = handler.get_xc_category_id("Sports")
    id_2 = handler.get_xc_category_id("Sports")
    assert id_1 == id_2


def test_different_categories_get_different_ids(handler: CategoryXCCategoryIDDatabaseHandler) -> None:
    """Different category names get different xc_category_ids."""
    assert handler.get_xc_category_id("Sports") != handler.get_xc_category_id("News")


def test_get_category_name(handler: CategoryXCCategoryIDDatabaseHandler) -> None:
    """get_category_name returns the correct name for a known id."""
    xc_id = handler.get_xc_category_id("Movies")
    assert handler.get_category_name(xc_id) == "Movies"


def test_get_category_name_missing(handler: CategoryXCCategoryIDDatabaseHandler) -> None:
    """get_category_name returns None for an unknown id."""
    assert handler.get_category_name(99999) is None


def test_get_all_categories_api_filters_by_in_use(handler: CategoryXCCategoryIDDatabaseHandler) -> None:
    """get_all_categories_api only returns categories that are in use."""
    sports_id = handler.get_xc_category_id("Sports")
    handler.get_xc_category_id("News")

    result = handler.get_all_categories_api(categories_in_use={sports_id})

    assert len(result) == 1
    assert result[0].category_id == str(sports_id)
    assert result[0].category_name == "Sports"
