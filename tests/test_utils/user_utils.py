import random
import string
from typing import TYPE_CHECKING

from acere.constants import API_V1_STR
from acere.instances.config import settings

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
else:
    TestClient = object


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def get_superuser_token_headers(client: TestClient) -> dict[str, str]:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    return {"Authorization": f"Bearer {a_token}"}
