"""Tests for scraper name-override endpoints."""

from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from acere.instances.ace_streams import get_ace_streams_db_handler
from acere.services.scraper.models import FoundAceStream
from tests.test_utils.ace import get_random_content_id

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
else:
    TestClient = object


@pytest.fixture(autouse=True)
def no_scrape_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    """Don't start a real scrape thread when the route saves an override."""
    monkeypatch.setattr(
        "acere.api.routes.api.scraper.get_ace_scraper",
        type("MockScraper", (), {"start_scrape_thread": lambda self: None}),
    )


def _add_stream(content_id: str, infohash: str | None) -> None:
    get_ace_streams_db_handler().update_stream(
        FoundAceStream(
            title="Original Title",
            content_id=content_id,
            infohash=infohash,
            tvg_id="",
            sites_found_on=["test"],
            last_scraped_time=datetime.now(tz=UTC),
        )
    )


def test_add_name_override_renames_by_content_id(client: TestClient) -> None:
    """Adding an override keyed by content_id updates the stream title immediately."""
    content_id = get_random_content_id()
    _add_stream(content_id, infohash=None)

    response = client.post(f"/api/v1/scraper/name-override/{content_id}", params={"name": "New Name"})

    assert response.status_code == HTTPStatus.OK
    stream = get_ace_streams_db_handler().get_by_content_id(content_id)
    assert stream is not None
    assert stream.title == "New Name"


def test_add_name_override_renames_by_infohash(client: TestClient) -> None:
    """Adding an override keyed by infohash updates the stream title immediately."""
    content_id = get_random_content_id()
    infohash = get_random_content_id()
    _add_stream(content_id, infohash=infohash)

    response = client.post(f"/api/v1/scraper/name-override/{infohash}", params={"name": "Newer Name"})

    assert response.status_code == HTTPStatus.OK
    stream = get_ace_streams_db_handler().get_by_content_id(content_id)
    assert stream is not None
    assert stream.title == "Newer Name"


def test_add_name_override_without_matching_stream(client: TestClient) -> None:
    """Overrides for unknown keys still save without error."""
    response = client.post(f"/api/v1/scraper/name-override/{get_random_content_id()}", params={"name": "Ghost"})

    assert response.status_code == HTTPStatus.OK
