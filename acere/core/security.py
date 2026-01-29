from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from acere.instances.config import settings
from acere.utils.logger import logger

ph = PasswordHasher()

ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:  # noqa: ANN401 We stringify subject
    expire = datetime.now(UTC) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
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
