from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm  # noqa: TC002 Will break everything otherwise

from acere import crud
from acere.api.deps import CurrentUser, SessionDep  # noqa: TC001 Will break everything otherwise
from acere.core import security
from acere.core.security import get_password_hash
from acere.instances.config import settings
from acere.models import Message, NewPassword, Token, UserPublic
from acere.utils.auth import (
    verify_password_reset_token,
)

router = APIRouter(tags=["Login"])


@router.post("/login/access-token")
def login_access_token(session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """OAuth2 compatible token login, get an access token for future requests."""
    user = crud.authenticate(session=session, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(access_token=security.create_access_token(user.id, expires_delta=access_token_expires))


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> CurrentUser:
    """Test access token."""
    return current_user


@router.post("/reset-password/")
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """Reset password."""
    username = verify_password_reset_token(token=body.token)
    if not username:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.get_user_by_username(session=session, username=username)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password
    session.add(user)
    session.commit()
    return Message(message="Password updated successfully")
