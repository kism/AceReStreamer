# Wait for background task
import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Any

import pytest

from acere.constants import OUR_TIMEZONE
from acere.database.handlers.quality_cache import AceQualityCacheHandler
from acere.database.models import AceStreamDBEntry
from acere.services.ace_quality import Quality
from tests.test_utils.ace import get_random_content_id

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

else:
    Path = object
    Generator = object


@pytest.fixture(autouse=True)
def set_external_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fixture to set EXTERNAL_URL for tests."""
    monkeypatch.setattr("acere.instances.config.settings.EXTERNAL_URL", "http://localhost:8000/")


@pytest.mark.asyncio
async def test_check_missing_quality_no_streams(
    quality_cache_handler: AceQualityCacheHandler,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test check_missing_quality when there are no streams."""
    handler = quality_cache_handler

    # Mock the ace streams handler to return empty list
    mock_ace_handler = type(
        "MockAceHandler",
        (),
        {"get_streams": lambda self: []},
    )()

    monkeypatch.setattr(
        "acere.database.handlers.quality_cache.get_ace_streams_db_handler",
        lambda: mock_ace_handler,
    )

    # Call check_missing_quality
    result = await handler.check_missing_quality(stream_delay=0, attempt_delay=0)
    assert result is True
    await asyncio.sleep(0.01)  # Bit sketchy
    assert handler._currently_checking_quality is False


@pytest.mark.asyncio
async def test_check_missing_quality_already_checking(
    quality_cache_handler: AceQualityCacheHandler,
) -> None:
    """Test check_missing_quality when already checking."""
    quality_cache_handler._currently_checking_quality = True
    assert await quality_cache_handler.check_missing_quality(stream_delay=0, attempt_delay=0) is False


@pytest.mark.asyncio
async def test_check_missing_quality_with_streams(
    quality_cache_handler: AceQualityCacheHandler,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test check_missing_quality with streams that need checking."""
    handler = quality_cache_handler
    content_ids: list[str] = [get_random_content_id() for _ in range(3)]  # Create test content IDs

    # Set up initial quality states
    handler.set_quality(content_ids[0], Quality(quality=-1, has_ever_worked=False))
    handler.set_quality(content_ids[1], Quality(quality=50, has_ever_worked=True))
    handler.set_quality(content_ids[2], Quality(quality=0, has_ever_worked=True))

    # Create mock streams
    mock_streams = [
        AceStreamDBEntry(
            id=i + 1,
            content_id=content_id,
            title=f"Stream {i + 1}",
            tvg_id=f"test{i + 1}.tv",
            infohash="",
            group_title="Test",
            last_scraped_time=datetime.now(tz=OUR_TIMEZONE),
        )
        for i, content_id in enumerate(content_ids)
    ]

    # Mock Ace Streams Handler
    mock_ace_handler = type(
        "MockAceHandler",
        (),
        {"get_streams": lambda self: mock_streams},
    )()
    monkeypatch.setattr(
        "acere.database.handlers.quality_cache.get_ace_streams_db_handler",
        lambda: mock_ace_handler,
    )

    # Mock HLS
    hls_calls: list[dict[str, Any]] = []

    async def mock_hls(path: str, *, authentication_override: bool = False) -> None:
        """Mock HLS function that tracks calls."""
        hls_calls.append({"path": path, "authentication_override": authentication_override})

    monkeypatch.setattr("acere.api.routes.hls.hls", mock_hls)

    # Call check_missing_quality
    result = await handler.check_missing_quality(stream_delay=0, attempt_delay=0)
    assert result is True

    # Wait for quality to be checked
    for _ in range(50):
        await asyncio.sleep(0.01)
        if not handler._currently_checking_quality:
            break

    assert len(hls_calls) >= 1  # hls() was called at least once

    for call in hls_calls:  # Verify authentication_override was set to True
        assert call["authentication_override"] is True

    checked_content_ids = {call["path"] for call in hls_calls}  # Extract checked content IDs
    assert content_ids[0] in checked_content_ids or content_ids[2] in checked_content_ids, (
        "Streams needing quality check were not checked"
    )
    assert content_ids[1] not in checked_content_ids, "Stream with good quality was incorrectly checked"


@pytest.mark.asyncio
async def test_check_missing_quality_with_exception(
    quality_cache_handler: AceQualityCacheHandler,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test check_missing_quality handles exceptions gracefully."""
    handler = quality_cache_handler

    # Create a mock stream
    content_id = get_random_content_id()
    mock_streams = [
        AceStreamDBEntry(
            id=1,
            content_id=content_id,
            title="Stream 1",
            tvg_id="test1.tv",
            infohash="",
            group_title="Test",
            last_scraped_time=datetime.now(tz=OUR_TIMEZONE),
        ),
    ]

    # Mock Ace Streams Handler
    mock_ace_handler = type(
        "MockAceHandler",
        (),
        {"get_streams": lambda self: mock_streams},
    )()

    monkeypatch.setattr(
        "acere.database.handlers.quality_cache.get_ace_streams_db_handler",
        lambda: mock_ace_handler,
    )

    # Mock HLS
    async def mock_hls_exception(path: str, *, authentication_override: bool = False) -> None:
        raise RuntimeError("Test exception")

    monkeypatch.setattr("acere.api.routes.hls.hls", mock_hls_exception)

    assert await handler.check_missing_quality(stream_delay=0, attempt_delay=0) is True

    for _ in range(50):
        await asyncio.sleep(0.01)
        if not handler._currently_checking_quality:
            break

    assert handler._currently_checking_quality is False
