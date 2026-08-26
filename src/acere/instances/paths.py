from typing import TYPE_CHECKING

from acere.instances import GlobalInstance
from acere.services.app_paths_helper import AppPathsHelper

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object

_instance_paths: GlobalInstance[AppPathsHelper] = GlobalInstance("AppPathsHelper")
get_app_path_handler = _instance_paths.get


def setup_app_path_handler(instance_path: Path) -> None:
    """Set up the instance path for the application."""
    _instance_paths.set(AppPathsHelper(instance_path=instance_path))
