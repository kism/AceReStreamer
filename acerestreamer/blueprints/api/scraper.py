"""Scraper API Blueprint."""

from http import HTTPStatus

from flask import Blueprint, Response, jsonify
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_scraper
from acerestreamer.services.authentication.helpers import assumed_auth_failure
from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint("acerestreamer_scraper_api", __name__)


@bp.route("/api/sources")
def api_streams_sources_flat() -> Response | WerkzeugResponse:
    """API endpoint to get the flat streams sources."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    sources = ace_scraper.get_scraper_sources_flat_api()
    sources_serialized = [source.model_dump() for source in sources]

    response = jsonify(sources_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/sources/check", methods=["POST"])
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
