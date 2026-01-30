from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object


class AppPathsHelper:
    def __init__(self, instance_path: Path) -> None:
        self.set_instance_path(instance_path)

    def set_instance_path(self, instance_path: Path) -> None:
        self._instance_path = instance_path
        self._ensure_dirs_exist()

    def _ensure_dirs_exist(self) -> None:
        dirs = [
            self._instance_path,
            self.scraper_cache_dir,
            self.tvg_logos_dir,
            self.playlists_dir,
            self.epg_data_dir,
        ]
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def instance_path(self) -> Path:
        return self._instance_path

    @property
    def scraper_cache_dir(self) -> Path:
        return self._instance_path / "scraper_cache"

    @property
    def tvg_logos_dir(self) -> Path:
        return self._instance_path / "tvg_logos"

    @property
    def playlists_dir(self) -> Path:
        return self._instance_path / "playlists"

    @property
    def epg_data_dir(self) -> Path:
        return self._instance_path / "epg_data"

    @property
    def settings_file(self) -> Path:
        return self._instance_path / "config.json"

    @property
    def database_file(self) -> Path:
        return self._instance_path / "acerestreamer.db"
