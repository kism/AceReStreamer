"""Module for generating a readme for adhoc mode."""

from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, HttpUrl

from acere.instances.paths import get_app_path_handler
from acere.version import PROGRAM_NAME, __version__

from .constants import M3U_URI_SCHEMES


class AdhocPlaylist(BaseModel):
    """Represents an ad-hoc playlist."""

    name: str
    type: str
    uri: str


def generate_readme(external_base_url: HttpUrl | None) -> None:
    """Generate README.md for adhoc mode."""
    path_handler = get_app_path_handler()
    result_playlists: dict[str, list[AdhocPlaylist]] = {}

    found_playlists = list((path_handler.playlists_dir).glob("*.m3u"))

    for found_playlist in found_playlists:
        playlist_type = next(
            (playlist_name for playlist_name in M3U_URI_SCHEMES if playlist_name in found_playlist.stem),
            "unknown",
        )

        playlist_name_nice = found_playlist.stem.replace(playlist_type, "").replace("_", " ").replace("-", " ").strip()

        if playlist_name_nice not in result_playlists:
            result_playlists[playlist_name_nice] = []
        result_playlists[playlist_name_nice].append(
            AdhocPlaylist(
                name=playlist_name_nice,
                type=playlist_type,
                uri=f"{external_base_url}/playlists/{found_playlist.name}",
            )
        )
        result_playlists[playlist_name_nice].sort(key=lambda x: x.type)

    env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=True)
    template = env.get_template("README.md.j2")
    readme_content = template.render(
        playlists=result_playlists,
        program_name=PROGRAM_NAME,
        version=__version__,
        time_generated=datetime.now(tz=UTC),
    )
    readme_content += "\n"
    with (path_handler.instance_path / "README.md").open("w", encoding="utf-8") as readme_file:
        readme_file.write(readme_content)
