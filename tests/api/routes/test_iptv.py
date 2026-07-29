"""Tests for IPTV playlist endpoints."""

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
else:
    TestClient = object


@pytest.mark.parametrize(
    "path",
    ["/iptv", "/iptv.m3u", "/iptv.m3u8", "/iptv-ts", "/iptv-ts.m3u", "/iptv-ts.m3u8"],
)
def test_iptv_playlist_routes(client: TestClient, path: str) -> None:
    """Test all IPTV playlist aliases (HLS and MPEG-TS) return an m3u playlist."""
    response = client.get(path)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["Content-Type"].startswith("application/vnd.apple.mpegurl")
    assert response.text.startswith("#EXTM3U")
