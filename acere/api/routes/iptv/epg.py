"""Blueprint for EPG Endpoints."""

from typing import Annotated

from fastapi import APIRouter, Query, Response

from acere.core.stream_token import verify_stream_token
from acere.instances.scraper import get_ace_scraper
from acere.services.xc.helpers import check_xc_auth

router = APIRouter(tags=["Media/XML"])


@router.get(
    "/epg",
    response_class=Response,
    name="epg_xml_1",
)
@router.get(
    "/epg.xml",
    response_class=Response,
    name="epg_xml_2",
)
def get_epg(token: Annotated[str, Query()] = "") -> Response:
    """Get the merged EPG data."""
    verify_stream_token(token)

    ace_scraper = get_ace_scraper()

    condensed_epg = ace_scraper.epg_handler.get_condensed_epg()

    return Response(
        content=condensed_epg,
        media_type="application/xml",
        headers={"Content-Disposition": 'attachment; filename="condensed_epg.xml"'},
    )


@router.get("/xmltv.php", response_class=Response, name="epg_xml_3")  # XC Standard
def get_epg_xc(username: Annotated[str, Query()] = "", password: Annotated[str, Query()] = "") -> Response:
    """Get the merged EPG data."""
    check_xc_auth(username, password)

    ace_scraper = get_ace_scraper()

    condensed_epg = ace_scraper.epg_handler.get_condensed_epg()

    return Response(
        content=condensed_epg,
        media_type="application/xml",
        headers={"Content-Disposition": 'attachment; filename="condensed_epg.xml"'},
    )
