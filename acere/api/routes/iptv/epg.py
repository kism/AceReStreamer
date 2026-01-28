"""Blueprint for EPG Endpoints."""

from typing import Annotated

from fastapi import APIRouter, Query, Response

from acere.core.stream_token import verify_stream_token
from acere.instances.epg import get_epg_handler
from acere.services.xc.helpers import check_xc_auth

router = APIRouter(tags=["Media/XML"])


@router.get(
    "/epg.xml",
    response_class=Response,
    name="epg_xml",
)
def get_epg(token: Annotated[str, Query()] = "") -> Response:
    """Get the merged EPG data."""
    verify_stream_token(token)

    condensed_epg = get_epg_handler().get_condensed_epg()

    return Response(
        content=condensed_epg,
        media_type="application/xml",
        headers={"Content-Disposition": 'attachment; filename="condensed_epg.xml"'},
    )


@router.get("/xmltv.php", response_class=Response, name="epg_xml_3")  # XC Standard
def get_epg_xc(username: Annotated[str, Query()] = "", password: Annotated[str, Query()] = "") -> Response:
    """Get the merged EPG data."""
    check_xc_auth(username, password)

    condensed_epg = get_epg_handler().get_condensed_epg()

    return Response(
        content=condensed_epg,
        media_type="application/xml",
        headers={"Content-Disposition": 'attachment; filename="condensed_epg.xml"'},
    )
