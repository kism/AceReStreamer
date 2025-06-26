"""Main Stream Site Blueprint."""

from http import HTTPStatus

from flask import Blueprint, Response, jsonify
from werkzeug.wrappers import Response as WerkzeugResponse

from ._obj_instances import ace_scraper
from .authentication_helpers import assumed_auth_failure
from .flask_helpers import get_current_app
from .logger import get_logger

current_app = get_current_app()

logger = get_logger(__name__)

bp = Blueprint("acerestreamer_stream_api", __name__)


# region /api/stream(s)
@bp.route("/api/stream/<path:ace_id>")
def api_stream(ace_id: str) -> Response | WerkzeugResponse:
    """API endpoint to get a specific stream by Ace ID."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    stream = ace_scraper.get_stream_by_ace_id(ace_id)

    response = jsonify(stream.model_dump())
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/streams/flat")
def api_streams_flat() -> Response | WerkzeugResponse:
    """API endpoint to get the flat streams."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_streams_flat()
    streams_serialized = [stream.model_dump() for stream in streams]

    response = jsonify(streams_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/streams/by_source")
def api_streams() -> Response | WerkzeugResponse:
    """API endpoint to get the streams."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_all_streams_by_source()
    streams_serialized = [stream.model_dump() for stream in streams]

    response = jsonify(streams_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/streams/by_source/<source_slug>")
def api_streams_by_source(source_slug: str) -> Response | WerkzeugResponse:
    """API endpoint to get the streams by source slug."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_streams_by_source(source_slug)
    if not streams:
        return jsonify({"error": "No streams found for this source"}, HTTPStatus.NOT_FOUND)

    streams_serialized = [stream.model_dump() for stream in streams]

    response = jsonify(streams_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/streams/health")
def api_streams_health() -> Response | WerkzeugResponse:
    """API endpoint to get the streams."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_streams_health()
    streams_dict = {ace_id: quality.model_dump() for ace_id, quality in streams.items()}

    response = jsonify(streams_dict)
    response.status_code = HTTPStatus.OK

    return response


@bp.route("/api/streams/health/check_all", methods=["POST"])
def api_streams_health_check_all() -> Response | WerkzeugResponse:
    """API endpoint to attempt to check all streams health."""
    started = ace_scraper.check_missing_quality()

    if started:
        response = jsonify({"message": "Health check started"})
        response.status_code = HTTPStatus.ACCEPTED
    else:
        response = jsonify({"error": "Health check already running"})
        response.status_code = HTTPStatus.CONFLICT

    return response
