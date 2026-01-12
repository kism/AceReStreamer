"""Tests for the AcePool service."""

import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from pydantic import HttpUrl

from acere.services.ace_pool.entry import AcePoolEntry
from acere.services.ace_pool.pool import AcePool
from acere.utils.ace import get_middleware_url
from tests.test_utils.ace import (
    create_mock_middleware_response,
    create_mock_stat_response,
    get_random_content_id,
)
from tests.test_utils.aiohttp import FakeSession

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
else:
    MockerFixture = object


def fill_pool(pool: AcePool) -> None:
    """Fill the AcePool to its maximum size for testing."""
    ace_address = pool.ace_address
    for i in range(1, pool.max_size + 1):
        pool.ace_instances[str(i)] = AcePoolEntry(
            ace_pid=i,
            ace_address=ace_address,
            content_id=get_random_content_id(),
            transcode_audio=False,
        )


@pytest.fixture(autouse=True)
def mock_no_poolboy_thread(mocker: MockerFixture) -> None:
    """Mock the ace_poolboy thread to avoid starting background threads in tests."""
    mocker.patch("acere.services.ace_pool.pool.threading.Thread")


@pytest.mark.asyncio
async def test_ace_pool_initialization(mocker: MockerFixture) -> None:
    """Test that AcePool initializes correctly."""
    # Mock the ace_poolboy thread to avoid starting background threads in tests
    mock_thread = mocker.patch("acere.services.ace_pool.pool.threading.Thread")

    # Create an AcePool instance
    pool = AcePool(instance_id="test")

    # Verify the pool is initialized with correct attributes
    assert pool._instance_id == "test"
    assert pool.ace_instances == {}
    assert pool.healthy is False
    assert pool.ace_version == "unknown"
    assert pool.max_size == 4  # Default from settings

    # Verify the poolboy thread was started
    mock_thread.assert_called_once()


@pytest.mark.asyncio
async def test_check_ace_running_healthy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test check_ace_running when AceStream is healthy."""
    # Create mock response data
    mock_response_data = {"result": {"version": "3.1.49"}}

    # Create fake session with the expected URL
    # Note: URL has double slash because ace_address has trailing slash
    fake_session = FakeSession(
        {
            "http://localhost:6878/webui/api/service?method=get_version": {
                "status": 200,
                "data": json.dumps(mock_response_data),
            }
        }
    )

    # Mock aiohttp.ClientSession in the pool module
    monkeypatch.setattr("acere.services.ace_pool.pool.aiohttp.ClientSession", lambda **kwargs: fake_session)

    pool = AcePool(instance_id="test")
    result = await pool.check_ace_running()

    # Verify the result
    assert result is True
    assert pool.healthy is True
    assert pool.ace_version == "3.1.49"


@pytest.mark.asyncio
async def test_check_ace_running_unhealthy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test check_ace_running when AceStream is not responding."""
    fake_session = FakeSession({})  # Empty dict means all URLs return 404

    # Mock aiohttp.ClientSession
    monkeypatch.setattr("acere.services.ace_pool.pool.aiohttp.ClientSession", lambda **kwargs: fake_session)

    pool = AcePool(instance_id="test")
    result = await pool.check_ace_running()

    # Verify the result
    assert result is False
    assert pool.healthy is False
    assert pool.ace_version == "unknown"


@pytest.mark.asyncio
async def test_get_available_instance_number() -> None:
    """Test getting an available instance number when pool is empty."""
    pool = AcePool(instance_id="test")

    instance_number = await pool.get_available_instance_number()
    assert instance_number == 1


@pytest.mark.asyncio
async def test_get_available_instance_number_full_pool_no_locked_in() -> None:
    """Test getting an available instance number when pool is full, no instance locked in."""
    pool = AcePool(instance_id="test")
    pool.max_size = 2  # Set max size to 2 for testing

    fill_pool(pool)

    instance_number = await pool.get_available_instance_number()
    assert instance_number is not None


@pytest.mark.asyncio
async def test_get_available_instance_number_full_pool() -> None:
    """Test getting an available instance number when pool is full."""
    pool = AcePool(instance_id="test")

    fill_pool(pool)

    datetime_now = datetime.now(UTC)

    for instance in pool.ace_instances.values():
        instance.date_started = datetime_now - timedelta(minutes=60)
        instance.date_last_used = datetime_now - timedelta(minutes=1)

    instance_number = await pool.get_available_instance_number()
    assert instance_number is None


@pytest.mark.asyncio
async def test_get_set_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    content_id = get_random_content_id()
    mock_playback_url = HttpUrl("http://localhost:6878/ace/m/whatever.m3u8")
    mock_stat_url = HttpUrl("http://localhost:6878/stat/whatever")
    mock_command_url = HttpUrl("http://localhost:6878/ace/cmd/whatever")

    mw_info_full = create_mock_middleware_response(
        playback_url=mock_playback_url,
        stat_url=mock_stat_url,
        command_url=mock_command_url,
        playback_session_id="session123",
    )

    # Create a minimal mock stat response
    mock_stat_response = create_mock_stat_response(
        playback_session_id="session123",
    )

    pool = AcePool(instance_id="test")

    middleware_url = get_middleware_url(
        ace_url=pool.ace_address,
        content_id=content_id,
        ace_pid=1,
        transcode_audio=pool.transcode_audio,
    )

    fake_session = FakeSession(
        {
            mock_command_url.encoded_string(): {
                "status": 200,
                "data": json.dumps({}),
            },
            mock_stat_url.encoded_string(): {
                "status": 200,
                "data": json.dumps({"response": mock_stat_response.model_dump(), "error": None}),
            },
            mock_playback_url.encoded_string(): {
                "status": 200,
                "data": "FAKE PLAYBACK DATA",
            },
            middleware_url: {
                "status": 200,
                "data": mw_info_full.model_dump_json(),
            },
        }
    )

    monkeypatch.setattr("acere.services.ace_pool.pool.aiohttp.ClientSession", lambda **kwargs: fake_session)
    monkeypatch.setattr("acere.services.ace_pool.entry.aiohttp.ClientSession", lambda **kwargs: fake_session)

    # Mark pool as healthy so stats queries work
    pool.healthy = True

    url_1 = await pool.get_instance_hls_url_by_content_id(content_id)
    url_2 = await pool.get_instance_hls_url_by_content_id(content_id)

    assert url_1 == url_2

    assert len(pool.ace_instances) == 1

    # Always gets the first instance in the dict
    instance = pool.ace_instances.values().__iter__().__next__()

    instance_by_pid = pool.get_instance_by_pid(instance.ace_pid)
    assert instance_by_pid is not None

    # Instance Api
    instances_api = pool.get_instances_api()
    assert len(instances_api.ace_instances) == 1

    instance_api = instances_api.ace_instances[0]

    new_pid = await pool.get_available_instance_number()
    assert new_pid != instance_api.ace_pid

    instance_by_content_id_api = pool.get_instance_by_content_id_api(content_id)
    assert instance_by_content_id_api is not None
    assert instance_by_content_id_api.ace_pid == instance_api.ace_pid

    instance_by_pid_api = pool.get_instance_by_pid_api(instance_api.ace_pid)
    assert instance_by_pid_api is not None
    assert instance_by_pid_api.ace_pid == instance_api.ace_pid

    # Stats
    stats = await pool.get_all_stats()
    assert len(stats) == pool.max_size  # Returns stats for all pool slots

    stats_by_pid = await pool.get_stats_by_pid(instance.ace_pid)
    assert stats_by_pid is not None

    stats_by_content_id = await pool.get_stats_by_content_id(content_id)
    assert stats_by_content_id is not None

    # Remove
    assert await pool.remove_instance_by_content_id(content_id, caller="Test")
