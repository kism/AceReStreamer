import uuid
from collections.abc import Generator  # noqa: TC003 Will break everything otherwise
from datetime import UTC, datetime
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session, select

from acere.constants import API_V1_STR
from acere.core import security
from acere.database.init import engine
from acere.database.models.user import TokenPayload, User
from acere.instances.config import settings
from acere.utils.logger import get_logger

logger = get_logger(__name__)

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{API_V1_STR}/login/access-token", auto_error=False)


def get_db() -> Generator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str | None, Depends(reusable_oauth2)]


def _get_first_superuser(session: Session) -> User:
    """Get the first superuser from the database for no-auth mode."""
    user = session.exec(select(User).where(User.is_superuser)).first()
    if not user:
        raise HTTPException(status_code=500, detail="No superuser found in database")
    return user


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    if settings.AUTH_DISABLED:
        return _get_first_superuser(session)

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except InvalidTokenError, ValidationError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    token_sub = uuid.UUID(token_data.sub) if token_data.sub else None
    user = session.get(User, token_sub)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if token_data.iat is not None and user.password_changed_at is not None:
        token_issued_at = datetime.fromtimestamp(token_data.iat, tz=UTC)
        if token_issued_at < user.password_changed_at:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user
