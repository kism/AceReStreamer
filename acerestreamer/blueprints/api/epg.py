"""Blueprint for EPG API Endpoints."""

from flask import Blueprint, Response, jsonify
from werkzeug.wrappers import Response as WerkzeugResponse

from acerestreamer.instances import ace_scraper

bp = Blueprint("acerestreamer_epg_api", __name__)

epg_handler = ace_scraper.epg_handler


@bp.route("/api/epgs", methods=["GET"])
def get_epgs() -> Response | WerkzeugResponse:
    """Get the list of EPGs."""
    epg_response = epg_handler.get_epgs_api()

    response = jsonify(epg_response.model_dump())
    response.status_code = 200
    return response
