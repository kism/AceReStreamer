"""Test versioning and file generation."""

import json
import tomllib
from pathlib import Path

from acere.version import __version__


def test_version_pyproject() -> None:
    """Verify version in pyproject.toml matches package version."""
    pyproject_path = Path("pyproject.toml")
    with pyproject_path.open("rb") as f:
        pyproject_toml = tomllib.load(f)
    assert pyproject_toml.get("project", {}).get("version") == __version__, (
        "Version in pyproject.toml does not match package version."
    )


def test_version_lock() -> None:
    """Verify version in uv.lock matches package version."""
    lock_path = Path("uv.lock")
    with lock_path.open("rb") as f:
        uv_lock = tomllib.load(f)

    package = next(
        (pkg for pkg in uv_lock.get("package", []) if pkg["name"] == "acere"),
        None,
    )
    assert package is not None, "acere not found in uv.lock"
    assert package["version"] == __version__


def test_frontend_package_json() -> None:
    """Verify version in frontend/package.json matches package version."""
    package_json_path = Path("frontend") / "package.json"

    with package_json_path.open("r", encoding="utf-8") as f:
        package_json = json.load(f)

    assert package_json.get("version") == __version__, (
        "Version in frontend/package.json does not match package version."
    )
