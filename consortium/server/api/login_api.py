from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    UnauthorizedError,
)
from consortium.server.exceptions.consortium_exceptions.user_accounts_consortium_exceptions import (
    UserAccountAuthenticationError,
)
from consortium.server.models.user_models import JSONWebTokenModel

router = APIRouter(
    prefix="/api/login",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
    },
    tags=["Login API"],
)

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
async def login_to_server(
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
