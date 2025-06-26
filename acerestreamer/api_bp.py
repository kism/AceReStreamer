"""API Blueprint."""

import threading
from http import HTTPStatus

from flask import Blueprint, Response, jsonify, request
from werkzeug.wrappers import Response as WerkzeugResponse

from ._obj_instances import ace_pool, ace_scraper
from .authentication_helpers import assumed_auth_failure
from .flask_helpers import get_current_app
from .logger import get_logger

current_app = get_current_app()

logger = get_logger(__name__)

bp = Blueprint("acerestreamer_api", __name__)


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


# region /api/ace_pool
@bp.route("/api/ace_pool")
def api_ace_pool() -> Response | WerkzeugResponse:
    """API endpoint to get the Ace pool."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    pool_list = ace_pool.get_instances_nice()
    pool_list_serialized = pool_list.model_dump()

    response = jsonify(pool_list_serialized)
    response.status_code = HTTPStatus.OK
    return response


@bp.route("/api/ace_pool/<path:ace_id>", methods=["GET", "DELETE"])
def api_ace_pool_by_id(ace_id: str) -> Response | WerkzeugResponse:
    """API endpoint to get or delete an Ace pool entry by Ace ID."""
    auth_failure = assumed_auth_failure()
    if auth_failure:
        return auth_failure

    instance_url = ace_pool.get_instance(ace_id)

    if instance_url is None:
        logger.error("Ace ID %s not found in pool", ace_id)
        return jsonify({"error": "Ace ID not found"}, HTTPStatus.NOT_FOUND)

    if request.method == "GET":
        return jsonify({"ace_url": instance_url}, HTTPStatus.OK)

    if request.method == "DELETE":
        ace_pool.remove_instance_by_ace_id(ace_id, caller="API")  # Assume success since we validated above
        return jsonify({"message": "Ace ID removed successfully"}, HTTPStatus.OK)

    return jsonify({"error": "Method not allowed"}, HTTPStatus.METHOD_NOT_ALLOWED)


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
