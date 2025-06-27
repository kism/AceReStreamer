"""Scraper API Blueprint."""

from http import HTTPStatus

from flask import Blueprint, Response, jsonify
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_scraper
from acerestreamer.services.authentication.helpers import assumed_auth_failure
from acerestreamer.utils.flask_helpers import get_current_app
from acerestreamer.utils.logger import get_logger

current_app = get_current_app()

logger = get_logger(__name__)

bp = Blueprint("acerestreamer_scraper_api", __name__)


# region /api/source(s)
@bp.route("/api/sources")
def api_streams_sources() -> Response | WerkzeugResponse:
    """API endpoint to get the streams sources."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_streams_sources()
    streams_serialized = streams.model_dump()

    response = jsonify(streams_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/sources/flat")
def api_streams_sources_flat() -> Response | WerkzeugResponse:
    """API endpoint to get the flat streams sources."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_streams_sources_flat()
    streams_serialized = [stream.model_dump() for stream in streams]

    response = jsonify(streams_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/source/<source_slug>")
def api_streams_source_by_slug(source_slug: str) -> Response | WerkzeugResponse:
    """API endpoint to get a specific stream source by slug."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    source = ace_scraper.get_streams_source(source_slug)
    if not source:
        return jsonify({"error": "Source not found"}, HTTPStatus.NOT_FOUND)

    response = jsonify(source.model_dump())
    response.status_code = HTTPStatus.OK
    return response
