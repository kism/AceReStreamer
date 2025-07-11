"""AcePool API Blueprint."""

from http import HTTPStatus

from flask import Blueprint, Response, jsonify, request
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_pool
from acerestreamer.services.authentication.helpers import assumed_auth_failure
from acerestreamer.utils.canned_responses import (
    instance_not_found_response,
    pid_not_found_response,
)
from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint("acerestreamer_acepool_api", __name__)


# region /api/ace-pool
@bp.route("/api/ace-pool", methods=["GET"])
def api_ace_pool() -> Response | WerkzeugResponse:
    """API endpoint to get the Ace pool."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    pool_list = ace_pool.get_instances_api()
    pool_list_serialized = pool_list.model_dump()

    response = jsonify(pool_list_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/ace-pool/content_id/<path:content_id>", methods=["GET", "DELETE"])
def api_ace_pool_content_id(content_id: str) -> Response | WerkzeugResponse:
    """API endpoint to get the Ace pool."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    instance = ace_pool.get_instance_by_content_id_api(content_id)

    if instance is None:
        return instance_not_found_response(content_id, in_what="Ace pool")

    if request.method == "DELETE":
        ace_pool.remove_instance_by_content_id(content_id, caller="API")
        response = jsonify({"message": "Ace ID removed successfully"})
        response.status_code = HTTPStatus.OK
    else:
        response = jsonify({"ace_url": instance})
        response.status_code = HTTPStatus.OK

    return response


@bp.route("/api/ace-pool/pid/<path:pid>", methods=["GET"])
def api_ace_pool_pid(pid: str) -> Response | WerkzeugResponse:
    """API endpoint to get the Ace pool."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    if not pid.isdigit():
        return pid_not_found_response(pid)

    pid_int = int(pid)
    instance = ace_pool.get_instance_by_pid_api(pid_int)
    if instance is None:  # noqa: SIM108 Clearer this way
        response = pid_not_found_response(pid)
    else:
        response = jsonify(ace_pool.get_instance_by_pid_api(pid_int))

    return response


# region /api/ace-pool/stats
@bp.route("/api/ace-pool/stats", methods=["GET"])
def api_ace_pool_stats() -> Response | WerkzeugResponse:
    """API endpoint to get Ace pool stats."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    ace_pool_stats = ace_pool.get_all_stats()
    response = jsonify(ace_pool_stats)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/ace-pool/stats/content_id/<path:content_id>", methods=["GET"])
def api_ace_pool_stats_content_id(content_id: str) -> Response | WerkzeugResponse:
    """API endpoint to get Ace pool stats by Ace content ID."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    ace_pool_stat = ace_pool.get_instance_by_content_id_api(content_id)

    if ace_pool_stat is None:
        return instance_not_found_response(content_id, in_what="Ace pool")

    response = jsonify(ace_pool_stat.model_dump())
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/ace-pool/stats/pid/<path:pid>", methods=["GET"])
def api_ace_pool_stats_pid(pid: str) -> Response | WerkzeugResponse:
    """API endpoint to get Ace pool stats by PID."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    try:
        pid_int = int(pid)
        ace_pool_stat = ace_pool.get_stats_by_pid(pid_int)

        if ace_pool_stat is None:
            return pid_not_found_response(pid)

        response = jsonify(ace_pool_stat.model_dump())
        response.status_code = HTTPStatus.OK
    except ValueError:
        response = pid_not_found_response(pid)

    return response
