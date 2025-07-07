"""AcePool API Blueprint."""

from http import HTTPStatus

from flask import Blueprint, Response, jsonify, request
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_pool
from acerestreamer.services.authentication.helpers import assumed_auth_failure
from acerestreamer.utils.canned_responses import (
    instance_not_found_response,
    invalid_method_response,
    invalid_query_parameters_response,
    pid_not_found_response,
)
from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)

bp = Blueprint("acerestreamer_acepool_api", __name__)


# region /api/ace-pool
def get_ace_pool() -> Response:
    """Get the Ace pool as a list."""
    if request.method != "GET":
        return invalid_method_response()

    pool_list = ace_pool.get_instances_api()
    pool_list_serialized = pool_list.model_dump()

    response = jsonify(pool_list_serialized)
    response.status_code = HTTPStatus.OK
    return response


def get_by_content_id(ace_content_id: str) -> Response:
    """Get an Ace instance by its content ID."""
    instance = ace_pool.get_instance_by_content_id_api(ace_content_id)

    if instance is None:
        return instance_not_found_response(ace_content_id, in_what="Ace pool")

    if request.method == "GET":
        response = jsonify({"ace_url": instance}, HTTPStatus.OK)
        response.status_code = HTTPStatus.OK
    elif request.method == "DELETE":
        ace_pool.remove_instance_by_ace_content_id(ace_content_id, caller="API")
        response = jsonify({"message": "Ace ID removed successfully"}, HTTPStatus.OK)
        response.status_code = HTTPStatus.OK
    else:
        response = invalid_method_response()

    return response


def get_by_pid(pid_str: str) -> Response:
    """Get an pool instance by its PID."""
    if request.method != "GET":
        response = invalid_method_response()

    try:
        pid_int = int(pid_str)
        instance = ace_pool.get_instance_by_pid_api(pid_int)
        if instance is None:
            response = pid_not_found_response(pid_str)
        else:
            response = jsonify(ace_pool.get_instance_by_pid_api(pid_int))
    except ValueError:
        response = pid_not_found_response(pid_str)

    return response


def get_stats() -> Response:
    """Get Ace pool stats."""
    if request.method != "GET":
        return invalid_method_response()

    ace_pool_stats = ace_pool.get_all_stats()
    response = jsonify(ace_pool_stats)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/ace-pool", methods=["GET", "DELETE"])
def api_ace_pool() -> Response | WerkzeugResponse:
    """API endpoint to get the Ace pool."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    # Whole Ace Pool
    if len(request.args) == 0:
        return get_ace_pool()

    response = invalid_query_parameters_response()

    # This only can take one query paramater
    if len(request.args) > 1:
        return response

    # Get Pool entry by content ID or PID
    if "content_id" in request.args:
        ace_content_id = request.args.get("ace_content_id", "")
        response = get_by_content_id(ace_content_id)
    elif "pid" in request.args:
        pid_str = request.args.get("pid", "")
        response = get_by_pid(pid_str)

    return response


# region /api/ace-pool/stats
def get_stats_by_pid(pid_str: str) -> Response:
    """Get Ace pool stats by PID."""
    if request.method != "GET":
        return invalid_method_response()

    try:
        pid_int = int(pid_str)
        ace_pool_stat = ace_pool.get_stats_by_pid(pid_int)

        if ace_pool_stat is None:
            return pid_not_found_response(pid_str)

        response = jsonify(ace_pool_stat.model_dump())
        response.status_code = HTTPStatus.OK
    except ValueError:
        response = pid_not_found_response(pid_str)

    return response


def get_stats_by_content_id(ace_content_id: str) -> Response:
    """Get Ace pool stats by content ID."""
    if request.method != "GET":
        return invalid_method_response()

    ace_pool_stat = ace_pool.get_instance_by_content_id_api(ace_content_id)

    if ace_pool_stat is None:
        return instance_not_found_response(ace_content_id, in_what="Ace pool")

    response = jsonify(ace_pool_stat.model_dump())
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/ace-pool/stats")
def api_ace_pool_stats() -> Response | WerkzeugResponse:
    """API endpoint to get Ace pool stats."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    if len(request.args) == 0:
        return get_stats()

    response = invalid_query_parameters_response()

    # This only can take one query paramater
    if len(request.args) > 1:
        return response

    # Get Pool entry by content ID or PID
    if "content_id" in request.args:
        ace_content_id = request.args.get("ace_content_id", "")
        response = get_stats_by_content_id(ace_content_id)
    elif "pid" in request.args:
        pid_str = request.args.get("pid", "")
        response = get_stats_by_pid(pid_str)

    return response
