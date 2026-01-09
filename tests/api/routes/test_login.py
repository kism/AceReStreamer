from http import HTTPStatus
from typing import TYPE_CHECKING

from acere.constants import API_V1_STR
from acere.instances.config import settings

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
else:
    TestClient = object


def test_get_access_token(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == HTTPStatus.OK
    assert "access_token" in tokens
    assert tokens["access_token"]


def test_get_access_token_incorrect_password(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": "incorrect",
    }
    r = client.post(f"{API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == HTTPStatus.BAD_REQUEST


def test_use_access_token(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    r = client.post(
        f"{API_V1_STR}/login/test-token",
        headers=superuser_token_headers,
    )
    result = r.json()
    assert r.status_code == HTTPStatus.OK
    assert "is_superuser" in result


def test_reset_password_invalid_token(client: TestClient, superuser_token_headers: dict[str, str]) -> None:
    data = {"new_password": "changethis", "token": "invalid"}
    r = client.post(
        f"{API_V1_STR}/reset-password/",
        headers=superuser_token_headers,
        json=data,
    )
    response = r.json()

    assert "detail" in response
    assert r.status_code == HTTPStatus.BAD_REQUEST
    assert response["detail"] == "Invalid token"
