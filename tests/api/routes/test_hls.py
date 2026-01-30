"""Tests for HLS streaming endpoints."""

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import pytest
from pydantic import HttpUrl

from acere.constants import STATIC_DIR
from acere.instances import epg as epg_instance_module
from acere.instances.config import settings
from acere.instances.paths import get_app_path_handler
from acere.services.epg.handler import EPGHandler
from acere.services.scraper import main as scraper_main_module
from tests.test_utils.ace import get_random_content_id
from tests.test_utils.aiohttp import FakeSession
from tests.test_utils.hls import generate_hls_m3u8
from tests.test_utils.user import create_random_user

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from fastapi.testclient import TestClient
    from sqlmodel import Session
else:
    TestClient = object
    Session = object
    Path = object
    Generator = object


# Sample HLS M3U8 content
SAMPLE_HLS_M3U8 = generate_hls_m3u8(5)

INVALID_HLS_RESPONSE = "ERROR: Something went wrong"


@pytest.fixture(autouse=True)
def setup_epg_handler(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Setup EPG handler before tests."""
    epg_handler = EPGHandler(instance_id="test_epg_handler")
    monkeypatch.setattr(epg_instance_module, "get_epg_handler", lambda: epg_handler)
    monkeypatch.setattr(scraper_main_module, "get_epg_handler", lambda: epg_handler)

    assert epg_instance_module.get_epg_handler() is epg_handler

    yield

    epg_handler.stop_all_threads()


@pytest.fixture
def valid_content_id() -> str:
    """Generate a valid content ID for testing."""
    return get_random_content_id()


@pytest.fixture
def normal_user_stream_token(client: TestClient, db: Session) -> str:
    """Get a valid stream token for a normal user."""
    user = create_random_user(db)
    return user.stream_token


def test_hls_without_token(client: TestClient, valid_content_id: str) -> None:
    """Test HLS endpoint without authentication token."""
    response = client.get(f"/hls/{valid_content_id}")

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert "Invalid or missing stream token" in response.json()["detail"]


def test_hls_with_invalid_token(client: TestClient, valid_content_id: str) -> None:
    """Test HLS endpoint with invalid authentication token."""
    response = client.get(f"/hls/{valid_content_id}?token=invalid_token")

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert "Invalid or missing stream token" in response.json()["detail"]


def test_hls_with_invalid_content_id(
    client: TestClient,
    normal_user_stream_token: str,
) -> None:
    """Test HLS endpoint with invalid content ID format."""
    invalid_content_id = "invalid_id"
    response = client.get(f"/hls/{invalid_content_id}?token={normal_user_stream_token}")

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Invalid content ID or infohash" in response.json()["detail"]


@pytest.mark.asyncio
async def test_hls_success(
    client: TestClient,
    normal_user_stream_token: str,
    valid_content_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test successful HLS stream retrieval."""
    # Mock ace pool to return a valid URL
    mock_hls_url = HttpUrl(f"http://localhost:6878/ace/getstream?id={valid_content_id}")

    # Create fake session with HLS response
    fake_session = FakeSession(
        {
            mock_hls_url.encoded_string(): {
                "status": 200,
                "data": SAMPLE_HLS_M3U8,
            }
        }
    )

    # Mock aiohttp ClientSession
    monkeypatch.setattr("acere.api.routes.hls.aiohttp.ClientSession", lambda **kwargs: fake_session)

    # Mock ace pool to return our test URL
    async def mock_get_instance_hls_url(self: Any, content_id: str) -> HttpUrl:
        return mock_hls_url

    monkeypatch.setattr(
        "acere.api.routes.hls.get_ace_pool",
        lambda: type("MockPool", (), {"get_instance_hls_url_by_content_id": mock_get_instance_hls_url})(),
    )

    response = client.get(f"/hls/{valid_content_id}?token={normal_user_stream_token}")

    assert response.status_code == HTTPStatus.OK
    assert "#EXTM3U" in response.text
    # Check that URLs have been rewritten to our external URL
    assert settings.EXTERNAL_URL in response.text


@pytest.mark.asyncio
async def test_hls_pool_full(
    client: TestClient,
    normal_user_stream_token: str,
    valid_content_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test HLS endpoint when Ace pool is full."""

    # Mock ace pool to return None (pool full)
    async def mock_get_instance_hls_url_none(self: Any, content_id: str) -> None:
        return None

    monkeypatch.setattr(
        "acere.api.routes.hls.get_ace_pool",
        lambda: type("MockPool", (), {"get_instance_hls_url_by_content_id": mock_get_instance_hls_url_none})(),
    )

    response = client.get(f"/hls/{valid_content_id}?token={normal_user_stream_token}")

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert "Ace pool is full" in response.json()["detail"]


@pytest.mark.asyncio
async def test_hls_invalid_response_from_ace(
    client: TestClient,
    normal_user_stream_token: str,
    valid_content_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test HLS endpoint when Ace returns invalid response."""
    mock_hls_url = HttpUrl(f"http://localhost:6878/ace/getstream?id={valid_content_id}")

    # Create fake session with invalid HLS response (no #EXTM3U)
    fake_session = FakeSession(
        {
            mock_hls_url.encoded_string(): {
                "status": 200,
                "data": INVALID_HLS_RESPONSE,
            }
        }
    )

    monkeypatch.setattr("acere.api.routes.hls.aiohttp.ClientSession", lambda **kwargs: fake_session)

    async def mock_get_instance_hls_url(self: Any, content_id: str) -> HttpUrl:
        return mock_hls_url

    monkeypatch.setattr(
        "acere.api.routes.hls.get_ace_pool",
        lambda: type("MockPool", (), {"get_instance_hls_url_by_content_id": mock_get_instance_hls_url})(),
    )

    response = client.get(f"/hls/{valid_content_id}?token={normal_user_stream_token}")

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Invalid HLS stream" in response.json()["detail"]


@pytest.mark.asyncio
async def test_hls_multi_success(
    client: TestClient,
    normal_user_stream_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test HLS multistream endpoint."""
    multistream_path = "test/multistream/path.m3u8"
    mock_content_id = get_random_content_id()
    mock_url = f"http://localhost:6878/hls/m/{multistream_path}"

    # Create fake session
    fake_session = FakeSession(
        {
            mock_url: {
                "status": 200,
                "data": SAMPLE_HLS_M3U8,
            }
        }
    )

    monkeypatch.setattr("acere.api.routes.hls.aiohttp.ClientSession", lambda **kwargs: fake_session)

    # Mock ace pool
    monkeypatch.setattr(
        "acere.api.routes.hls.get_ace_pool",
        lambda: type("MockPool", (), {"get_instance_by_multistream_path": lambda self, path: mock_content_id})(),
    )

    response = client.get(f"/hls/m/{multistream_path}?token={normal_user_stream_token}")

    assert response.status_code == HTTPStatus.OK
    assert "#EXTM3U" in response.text


@pytest.mark.asyncio
async def test_ace_content_success(
    client: TestClient,
    normal_user_stream_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Ace content proxy endpoint."""
    content_path = "test_content_id/segment1.ts"
    mock_ts_data = b"FAKE TS DATA"
    mock_url = f"http://localhost:6878/ace/c/{content_path}"

    # Create fake session
    fake_session = FakeSession(
        {
            mock_url: {
                "status": 200,
                "data": mock_ts_data,
            }
        }
    )

    monkeypatch.setattr("acere.api.routes.hls.aiohttp.ClientSession", lambda **kwargs: fake_session)

    response = client.get(f"/ace/c/{content_path}?token={normal_user_stream_token}")

    assert response.status_code == HTTPStatus.OK
    assert response.content == mock_ts_data
    assert response.headers["Content-Type"] == "video/MP2T"


@pytest.mark.asyncio
async def test_hls_content_success(
    client: TestClient,
    normal_user_stream_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test HLS content proxy endpoint."""
    content_path = "test_content_id/segment1.ts"
    mock_ts_data = b"FAKE TS DATA"
    mock_url = f"http://localhost:6878/hls/c/{content_path}"

    # Create fake session
    fake_session = FakeSession(
        {
            mock_url: {
                "status": 200,
                "data": mock_ts_data,
            }
        }
    )

    monkeypatch.setattr("acere.api.routes.hls.aiohttp.ClientSession", lambda **kwargs: fake_session)

    response = client.get(f"/hls/c/{content_path}?token={normal_user_stream_token}")

    assert response.status_code == HTTPStatus.OK
    assert response.content == mock_ts_data


def test_tvg_logo_with_existing_file(
    client: TestClient,
    normal_user_stream_token: str,
    temp_instance_dir: Path,
) -> None:
    """Test TVG logo endpoint with existing logo file."""
    # Create a test logo file
    logo_filename = "test_logo.png"
    logo_path = get_app_path_handler().tvg_logos_dir / logo_filename
    logo_path.parent.mkdir(parents=True, exist_ok=True)
    logo_path.write_bytes(b"FAKE PNG DATA")

    response = client.get(f"/tvg-logo/{logo_filename}?token={normal_user_stream_token}")

    assert response.status_code == HTTPStatus.OK
    assert response.content == b"FAKE PNG DATA"

    # Cleanup
    logo_path.unlink()


def test_tvg_logo_fallback_to_default(
    client: TestClient,
    normal_user_stream_token: str,
    temp_instance_dir: Path,
) -> None:
    """Test TVG logo endpoint falls back to default logo when file doesn't exist."""
    # Create a default logo file for testing
    default_logo = STATIC_DIR / "default_tvg_logo.png"
    default_logo.parent.mkdir(parents=True, exist_ok=True)
    default_logo.write_bytes(b"DEFAULT PNG DATA")

    non_existent_logo = "non_existent_logo.png"

    response = client.get(f"/tvg-logo/{non_existent_logo}?token={normal_user_stream_token}")

    assert response.status_code == HTTPStatus.OK
    # Should serve default logo
    assert response.headers["Cache-Control"] == "public, max-age=3600"
    assert response.content == b"DEFAULT PNG DATA"

    # Cleanup
    default_logo.unlink()


@pytest.mark.asyncio
async def test_xc_m3u8_success(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test XC API m3u8 endpoint with valid credentials."""
    user = create_random_user(db)
    xc_id = 12345
    mock_content_id = get_random_content_id()

    # Mock the database handler to return our content_id
    monkeypatch.setattr(
        "acere.api.routes.hls.get_ace_streams_db_handler",
        lambda: type("MockHandler", (), {"get_content_id_by_xc_id": lambda self, xc_id: mock_content_id})(),
    )

    # Mock the HLS URL retrieval
    mock_hls_url = HttpUrl(f"http://localhost:6878/ace/getstream?id={mock_content_id}")
    fake_session = FakeSession(
        {
            mock_hls_url.encoded_string(): {
                "status": 200,
                "data": SAMPLE_HLS_M3U8,
            }
        }
    )

    monkeypatch.setattr("acere.api.routes.hls.aiohttp.ClientSession", lambda **kwargs: fake_session)

    async def mock_get_instance_hls_url(self: Any, content_id: str) -> HttpUrl:
        return mock_hls_url

    monkeypatch.setattr(
        "acere.api.routes.hls.get_ace_pool",
        lambda: type("MockPool", (), {"get_instance_hls_url_by_content_id": mock_get_instance_hls_url})(),
    )

    # Test with path parameters
    response = client.get(f"/{user.username}/{user.stream_token}/{xc_id}.m3u8")

    assert response.status_code == HTTPStatus.OK
    assert "#EXTM3U" in response.text


def test_xc_m3u8_invalid_xc_id(
    client: TestClient,
    normal_user_stream_token: str,
    db: Session,
) -> None:
    """Test XC API m3u8 endpoint with invalid XC ID format."""
    user = create_random_user(db)

    response = client.get(f"/{user.username}/{user.stream_token}/invalid_id.m3u8")

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "invalid XC ID" in response.json()["detail"]


def test_xc_m3u8_invalid_credentials(client: TestClient) -> None:
    """Test XC API m3u8 endpoint with invalid credentials."""
    response = client.get("/invalid_user/invalid_token/12345.m3u8")

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "Invalid username or password" in response.json()["detail"]
