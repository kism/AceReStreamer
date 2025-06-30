"""Flask helpers for AceReStreamer."""

from http import HTTPStatus
from pathlib import Path
from typing import Any, cast

from flask import Flask, Response, current_app, send_file
from flask_caching import Cache

from acerestreamer.config import AceReStreamerConf
from acerestreamer.utils.constants import STATIC_DIRECTORY
from acerestreamer.utils.logger import get_logger

DEFAULT_CACHE_DURATION = 60 * 60 * 24  # 1 day in seconds

logger = get_logger(__name__)
cache = Cache(config={"DEBUG": False, "CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": DEFAULT_CACHE_DURATION})


class FlaskAceReStreamer(Flask):
    """Extend flask to add out config object to the app object."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Extend flask to add out config object to the app object."""
        super().__init__(*args, **kwargs)

        self.are_conf = AceReStreamerConf.load_config(Path(self.instance_path) / "config.json")
        self.are_conf.write_config(Path(self.instance_path) / "config.json")


def get_current_app() -> FlaskAceReStreamer:
    """Get the current app object."""
    return cast("FlaskAceReStreamer", current_app)


def check_static_folder(static_folder: str | Path | None) -> None:
    """Check if the static folder exists and favicon is not a Git LFS pointer file."""
    if static_folder is None:
        logger.error("No static folder provided, probably an issue.")
        return

    static_folder = Path(static_folder) if isinstance(static_folder, str) else static_folder

    if not static_folder.exists():
        try:
            with (Path(static_folder) / "favicon.ico").open() as f:
                if "version " in f.read():
                    logger.error(
                        "The favicon.ico file is a Git LFS pointer file, the web fonts are probably also wrong too.\n"
                        "Please run 'git lfs install' 'git lfs pull' to download the actual file."
                    )
        except UnicodeDecodeError:
            pass  # All good, not a pointer file


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for the Flask app."""

    @app.route("/favicon.ico")
    def favicon() -> Response:
        """Serve the favicon."""
        file = STATIC_DIRECTORY / "favicon.ico"
        return send_file(file, mimetype="image/x-icon")

    @app.errorhandler(HTTPStatus.NOT_FOUND)
    def not_found_error(error: HTTPStatus) -> Response:  # noqa: ARG001
        """Handle 404 errors."""
        file = STATIC_DIRECTORY / "404.html"

        response = send_file(file, mimetype="text/html")
        response.status_code = HTTPStatus.NOT_FOUND

        return response

    @app.errorhandler(HTTPStatus.UNAUTHORIZED)
    def unauthorized_error(error: HTTPStatus) -> Response:  # noqa: ARG001
        """Handle 401 errors."""
        file = STATIC_DIRECTORY / "401.html"

        response = send_file(file, mimetype="text/html")
        response.status_code = HTTPStatus.UNAUTHORIZED

        return response
