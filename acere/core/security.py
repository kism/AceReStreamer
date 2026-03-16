from datetime import UTC, datetime
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from acere.instances.config import settings
from acere.utils.logger import logger

ph = PasswordHasher()

ALGORITHM = "HS256"


def create_access_token(subject: str | Any) -> str:  # noqa: ANN401 We stringify subject
    now = datetime.now(UTC)
    to_encode: dict[str, Any] = {"sub": str(subject), "iat": now}

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hash=hashed_password, password=plain_password)
    except VerifyMismatchError:
        logger.debug("User entered the wrong password")
        return False
    except Exception as e:  # noqa: BLE001 We have captured specific exceptions above
        logger.warning(f"Unhandled password verification error: {e}")

    return False


def get_password_hash(password: str) -> str:
    return ph.hash(password)
