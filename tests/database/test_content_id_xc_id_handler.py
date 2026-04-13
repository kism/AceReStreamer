from typing import TYPE_CHECKING

import pytest
from sqlmodel import create_engine

from acere.database.handlers.content_id_xc_id import ContentIdXcIdDatabaseHandler
from tests.test_utils.ace import get_random_content_id

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object


@pytest.fixture
def handler(tmp_path: Path) -> ContentIdXcIdDatabaseHandler:
    """Fixture for ContentIdXcIdDatabaseHandler."""
    test_engine = create_engine(f"sqlite:///{tmp_path / 'test_xc_mapping.db'}", echo=False)
    return ContentIdXcIdDatabaseHandler(test_engine=test_engine)


def test_get_or_create_assigns_stable_id(handler: ContentIdXcIdDatabaseHandler) -> None:
    """Same content_id always returns same xc_id."""
    cid = get_random_content_id()
    xc_id_1 = handler.get_or_create_xc_id(cid)
    xc_id_2 = handler.get_or_create_xc_id(cid)
    assert xc_id_1 == xc_id_2


def test_different_content_ids_get_different_xc_ids(handler: ContentIdXcIdDatabaseHandler) -> None:
    """Different content_ids get different xc_ids."""
    cid_a = get_random_content_id()
    cid_b = get_random_content_id()
    xc_a = handler.get_or_create_xc_id(cid_a)
    xc_b = handler.get_or_create_xc_id(cid_b)
    assert xc_a != xc_b


def test_reverse_lookup(handler: ContentIdXcIdDatabaseHandler) -> None:
    """get_content_id_by_xc_id returns correct content_id."""
    cid = get_random_content_id()
    xc_id = handler.get_or_create_xc_id(cid)
    assert handler.get_content_id_by_xc_id(xc_id) == cid


def test_reverse_lookup_missing(handler: ContentIdXcIdDatabaseHandler) -> None:
    """get_content_id_by_xc_id returns None for unknown xc_id."""
    assert handler.get_content_id_by_xc_id(99999) is None


def test_mapping_survives_independent_of_stream_table(handler: ContentIdXcIdDatabaseHandler) -> None:
    """Mapping persists — xc_id stays same even if called again later."""
    cid = get_random_content_id()
    xc_id_first = handler.get_or_create_xc_id(cid)

    # Simulate "stream deleted, re-scraped" by just calling again
    xc_id_again = handler.get_or_create_xc_id(cid)
    assert xc_id_first == xc_id_again
