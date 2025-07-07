"""Main Stream Site Blueprint."""

from http import HTTPStatus

from flask import Blueprint, Response, jsonify
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_scraper
from acerestreamer.services.authentication.helpers import assumed_auth_failure
from acerestreamer.utils.flask_helpers import get_current_app
from acerestreamer.utils.logger import get_logger

current_app = get_current_app()

logger = get_logger(__name__)

bp = Blueprint("acerestreamer_stream_api", __name__)


# region /api/stream(s)
@bp.route("/api/streams/content_id/<path:ace_content_id>")
def api_stream(ace_content_id: str) -> Response | WerkzeugResponse:
    """API endpoint to get a specific stream by Ace ID."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    stream = ace_scraper.get_stream_by_ace_content_id_api(ace_content_id)

    response = jsonify(stream.model_dump())
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/streams")
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


@bp.route("/api/streams/health", methods=["GET"])
def api_streams_health() -> Response | WerkzeugResponse:
    """API endpoint to get the streams."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    streams = ace_scraper.get_streams_health()
    streams_dict = {ace_content_id: quality.model_dump() for ace_content_id, quality in streams.items()}

    response = jsonify(streams_dict)
    response.status_code = HTTPStatus.OK

    return response
