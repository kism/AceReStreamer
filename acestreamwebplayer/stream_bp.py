"""Blueprint one's object..."""

from http import HTTPStatus

import requests
from flask import Blueprint, Response, jsonify, render_template

from .flask_helpers import get_current_app
from .logger import get_logger
from .scraper import AceScraper

# Modules should all setup logging like this so the log messages include the modules name.
# If you were to list all loggers with something like...
# `loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]`
# Before creating this object, you would not see a logger with this modules name (acestreamwebplayer.this_module_name)
logger = get_logger(__name__)  # Create a logger: acestreamwebplayer.this_module_name, inherit config from root logger

# Register this module (__name__) as available to the blueprints of acestreamwebplayer, I think https://flask.palletsprojects.com/en/3.0.x/blueprints/
bp = Blueprint("acestreamwebplayer", __name__)

ace_scraper: AceScraper | None = None
current_app = get_current_app()


# KISM-BOILERPLATE:
# So regarding current_app, have a read of https://flask.palletsprojects.com/en/3.0.x/appcontext/
# This function is a bit of a silly example, but often you need to do things to initialise the module.
# You can't use the current_app object outside of a function since it behaves a bit weird, even if
#   you import the module under `with app.app_context():`
# So we call this to set globals in this module.
# You don't need to use this to set every variable as current_app will work fine in any function.
def start_scraper() -> None:
    """Method to 'configure' this module. Needs to be called under `with app.app_context():` from __init__.py."""
    global ace_scraper  # noqa: PLW0603 Necessary evil as far as I can tell, could move to all objects but eh...
    ace_scraper = AceScraper(current_app.aw_conf.app.site_list)  # Create the object with the config from the app object


@bp.route("/stream/<path:path>")
def webplayer_stream(path: str) -> tuple[str, int]:
    """Render the webpage for a stream."""
    stream_url = f"{current_app.config['SERVER_NAME']}/hls/{path}"

    return render_template(
        "stream.html.j2",
        stream_url=stream_url,
        stream_id=path,
    ), HTTPStatus.OK


@bp.route("/hls/<path:path>")
def hls_stream(path: str) -> tuple[Response, int]:
    """Reverse proxy the HLS from Ace."""
    url = f"{current_app.aw_conf.app.ace_address}/ace/manifest.m3u8?content_id={path}"

    logger.debug("HLS stream requested for path: %s", path)

    resp = requests.get(url, timeout=10, stream=True)
    excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]

    content_str = resp.content.decode("utf-8", errors="replace")

    if "#EXTM3U" not in content_str:
        logger.error("Invalid HLS stream received for path: %s", path)
        return jsonify({"error": "Invalid HLS stream"}), HTTPStatus.BAD_REQUEST

    # Replace the base URL in the stream with the new address
    # The docker container for acestream will always be localhost:6878
    content_str = content_str.replace("http://localhost:6878", current_app.config["SERVER_NAME"])

    return Response(content_str, resp.status_code, headers), HTTPStatus.OK


@bp.route("/ace/c/<path:path>")
def ace_content(path: str) -> tuple[Response, int]:
    """Reverse proxy the Ace content."""
    url = f"{current_app.aw_conf.app.ace_address}/ace/c/{path}"

    logger.debug("Ace content requested for path: %s", path)

    resp = requests.get(url, timeout=10, stream=True)
    excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]

    return Response(resp.content, resp.status_code, headers), HTTPStatus.OK

@bp.route("/api/v1/streams")
def api_streams() -> tuple[Response, int]:
    """API endpoint to get the streams."""
    if not ace_scraper:
        logger.error("Scraper object not initialized.")
        return jsonify({"error": "Scraper not initialized"}), HTTPStatus.INTERNAL_SERVER_ERROR

    streams = ace_scraper.get_streams()

    return jsonify(streams), HTTPStatus.OK
