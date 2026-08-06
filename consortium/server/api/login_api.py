from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions import (
    UserAccountAuthenticationError,
)
from consortium.server.models.user_models import JSONWebTokenModel

router = APIRouter(
    prefix="/api/login",
    responses={
        401: {"description": "Unauthorized"},
    },
    tags=["Login"],
)
limiter = Limiter(key_func=get_remote_address)

_user_accounts_service = server_singletons.user_accounts_service
_users_service = server_singletons.users_service


@router.post(
    "",
    responses={
        200: {"model": JSONWebTokenModel},
    },
    # This allows us to use the type annotations in the function signature because
    # Response is not a valid Pydantic model.
    response_model=None,
)
@limiter.limit("5/minute")
async def login_to_server(
    request: Request,  # Declaring request here is necessary for the rate limiter
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> JSONWebTokenModel | Response:
    try:
        user = _users_service.login_user(
            username=form_data.username,
            password=form_data.password,
        )
        # Note: That if an already logged in user attempts to login again we return
        # another new JWT
        return JSONWebTokenModel(**user.json_web_token.to_json())
    except UserAccountAuthenticationError:
        # This is the only api endpoint that does not require a value and hence will
        # not by default automatically return an empty 401 to unauthenticated requests.
        # Therefore, we need to manually return an empty 401 on unsuccessful login to
        # prevent C2 server fingerprinting.
        return Response(status_code=401)
