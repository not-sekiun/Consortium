from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    UnauthorizedError,
)
from consortium.server.exceptions.api_exceptions.login_api_exceptions import (
    AlreadyLoggedInError,
)
from consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions import (
    UserAccountAuthenticationError,
)
from consortium.server.models.user_models import JSONWebTokenModel
from consortium.server.server_dependencies import is_user_logged_in

router = APIRouter(
    prefix="/api/login",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
    },
    tags=["Login API"],
)

user_accounts_service = server_singletons.user_accounts_service
users_service = server_singletons.users_service

_already_logged_in_error = AlreadyLoggedInError()


@router.post(
    "",
    responses={
        200: {"model": JSONWebTokenModel},
        409: {"model": _already_logged_in_error.to_pydantic_model()},
    },
    # This allows us to use the type annotations in the function signature because
    # Response is not a valid Pydantic model.
    response_model=None,
)
async def login_to_server(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    is_user_logged_in_bool: Annotated[bool, Depends(is_user_logged_in)],
) -> JSONWebTokenModel | Response:
    # Since /api/login is the only API  endpoint that does not require a token, neither
    # our middleware nor our authorization dependencies will guarantee the identity of
    # the requester. Therefore, in this API endpoint specifically we need to manually
    # check if the user is already authenticated and return an actual error response.
    if is_user_logged_in_bool:
        raise AlreadyLoggedInError

    try:
        user = users_service.login_user(
            username=form_data.username,
            password=form_data.password,
        )
        return JSONWebTokenModel(**user.json_web_token.to_json())
    except UserAccountAuthenticationError:
        # This is the only api endpoint that does not require a token and hence will
        # not by default automatically return an empty 401 to unauthenticated requests.
        # Therefore, we need to manually return an empty 401 on unsuccessful login to
        # prevent C2 server fingerprinting.
        return Response(status_code=401)
