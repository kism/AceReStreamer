"""Test configuration and fixtures.

This module MUST set up the test environment before any application imports.
"""

import os
import shutil
import tempfile
from pathlib import Path

# CRITICAL: Set environment variables BEFORE any acere imports
# This must happen at module level, before pytest fixtures
# Prevent .env file from being loaded during tests
os.environ["ACERE_TESTING"] = "1"

_test_instance_dir = Path(tempfile.mkdtemp(prefix="acere_test_"))
os.environ["INSTANCE_DIR"] = str(_test_instance_dir)

# Create necessary subdirectories
(_test_instance_dir / "tvg_logos").mkdir(exist_ok=True)
(_test_instance_dir / "epg").mkdir(exist_ok=True)
(_test_instance_dir / "playlists").mkdir(exist_ok=True)
(_test_instance_dir / "scraper_cache").mkdir(exist_ok=True)

# Create a minimal test config with test superuser password
config_file = _test_instance_dir / "config.json"
shutil.copyfile(
    Path(__file__).parent / "configs" / "test_valid.json",
    config_file,
)

# NOW we can import the application modules
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from acere.core.db import engine, init_db
from acere.instances.config import settings
from acere.main import app
from acere.models import User
from tests.utils.user import authentication_token_from_username
from tests.utils.utils import get_superuser_token_headers

# Store the test password before init_db clears it
TEST_SUPERUSER_PASSWORD = "pytestpassword123"


@pytest.fixture(scope="session", autouse=True)
def temp_instance_dir() -> Generator[Path]:
    """Provide the temporary instance directory for tests."""
    yield _test_instance_dir

    # Cleanup: Remove the temporary directory after all tests
    if _test_instance_dir.exists() and _test_instance_dir.name.startswith(
        "acere_test_"
    ):
        shutil.rmtree(_test_instance_dir)


@pytest.fixture(scope="session", autouse=True)
def db(temp_instance_dir: Path) -> Generator[Session]:
    with Session(engine) as session:
        init_db(session)
        # After init_db, restore the password for tests to use
        settings.FIRST_SUPERUSER_PASSWORD = TEST_SUPERUSER_PASSWORD
        yield session
        statement = delete(User)
        session.exec(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_username(
        client=client, username="pytestuser", db=db
    )
