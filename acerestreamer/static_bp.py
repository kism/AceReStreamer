"""Fix weird problems with static files in Flask."""

from pathlib import Path

from flask import Blueprint, Response, send_from_directory

bp = Blueprint("acerestreamer_static_fix", __name__)


STATIC_DIR = Path(__file__).parent / "static"


@bp.route("/static/fonts/<path:filename>")
def static_fonts(filename: str) -> Response:
    """Serve static font files, fix the MIME type issue."""
    return send_from_directory(STATIC_DIR / "fonts", filename, mimetype="font/woff2")
