import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

from sqlmodel import Session, select

from acere.constants import API_V1_STR
from acere.models import User

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
else:
    TestClient = object


def test_create_user(client: TestClient, db: Session) -> None:
    r = client.post(
        f"{API_V1_STR}/private/users/",
        json={
            "username": "pytestuser",
            "password": "password123",
            "full_name": "Pollo Listo",
        },
    )

    assert r.status_code == HTTPStatus.OK

    data = r.json()

    user = db.exec(select(User).where(User.id == uuid.UUID(data["id"]))).first()

    assert user
    assert user.username == "pytestuser"
    assert user.full_name == "Pollo Listo"
