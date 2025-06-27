"""Health API Blueprint."""

import threading
from http import HTTPStatus

from flask import Blueprint, Response, jsonify
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.services.authentication.helpers import assumed_auth_failure
from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint("acerestreamer_health_api", __name__)


@bp.route("/api/health")
def api_health() -> Response | WerkzeugResponse:
    """API endpoint to check the health of the service."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    threads_enumerated = threading.enumerate()
    thread_list = [{"name": thread.name, "is_alive": thread.is_alive()} for thread in threads_enumerated]
    threads = {"threads": thread_list}
    response = jsonify(threads)
    response.status_code = HTTPStatus.OK
    return response
