from typing import TYPE_CHECKING

from acere.services.app_paths_helper import AppPathsHelper

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object

_instance_paths: AppPathsHelper | None = None


def get_app_path_handler() -> AppPathsHelper:
    """Get the current instance path."""
    if _instance_paths is None:
        msg = "Instance path not set up yet."
        raise RuntimeError(msg)
    return _instance_paths


def setup_app_path_handler(instance_path: Path) -> None:
    """Set up the instance path for the application."""
    global _instance_paths  # noqa: PLW0603
    _instance_paths = AppPathsHelper(instance_path=instance_path)
