"""Test configuration and fixtures.

This module MUST set up the test environment before any application imports.
"""

import os
import shutil
import tempfile
from pathlib import Path

from sqlmodel import create_engine

from acere.instances.paths import get_app_path_handler, setup_app_path_handler

# CRITICAL: Set environment variables BEFORE any acere imports
# This must happen at module level, before pytest fixtures
# Prevent .env file from being loaded during tests
os.environ["ACERE_TESTING"] = "1"

_test_instance_dir = Path(tempfile.mkdtemp(prefix="acere_test_"))
os.environ["INSTANCE_DIR"] = str(_test_instance_dir)

setup_app_path_handler(instance_path=_test_instance_dir)
path_handler = get_app_path_handler()

# Create a minimal test config
config_file = path_handler.settings_file
shutil.copyfile(
    Path(__file__).parent / "configs" / "test_valid.json",
    config_file,
)

# NOW we can import the application modules
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from acere.database.handlers.quality_cache import AceQualityCacheHandler
from acere.database.init import init_db
from acere.main import app

if TYPE_CHECKING:
    from collections.abc import Generator
else:
    Generator = object


@pytest.fixture(scope="session", autouse=True)
def temp_instance_dir() -> Generator[Path]:
    """Provide the temporary instance directory for tests."""
    yield _test_instance_dir

    # Cleanup: Remove the temporary directory after all tests
    if _test_instance_dir.exists() and _test_instance_dir.name.startswith("acere_test_"):
        shutil.rmtree(_test_instance_dir)


@pytest.fixture(scope="session", autouse=True)
def db(temp_instance_dir: Path) -> None:
    init_db()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def quality_cache_handler(tmp_path: Path) -> Generator[AceQualityCacheHandler, None, None]:
    """Fixture for AceQualityCacheHandler."""
    db_path = tmp_path / "test_quality_cache.db"
    test_engine = create_engine(f"sqlite:///{db_path}", echo=False)

    yield AceQualityCacheHandler(test_engine=test_engine)

    test_engine.dispose()
    db_path.unlink(missing_ok=True)
