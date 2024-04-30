from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.http_exceptions import UnauthorizedError
from consortium.server.exceptions.login_api_exceptions import AlreadyLoggedInError
from consortium.server.models.user_models import JSONWebTokenModel
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import is_user_logged_in

router = APIRouter(
    prefix="/api/login",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
    },
)
user_accounts_service = server_singletons.user_accounts_service
users_service = server_singletons.users_service


@router.post(
    "",
    responses={
        200: {"model": JSONWebTokenModel},
        409: {"model": AlreadyLoggedInError().to_pydantic_model()},
    },
    # This allows us to use the type annotations in the function signature as Response
    # is not a valid Pydantic model.
    response_model=None,
)
async def login_to_server(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    is_user_logged_in_bool: Annotated[bool, Depends(is_user_logged_in)],
) -> JSONWebTokenModel | Response:
    # Since /api/login is the only API  endpoint that does not require a token, neither
    # our middleware nor our authorization dependencies will guarantee the identity of
    # the requester. Therefore, in this API endpoint specifically we need to manually
    # check if the user is already authenticated and return an actual error response.
    if is_user_logged_in_bool:
        raise AlreadyLoggedInError

    # Handler login flow for unauthorized users
    for account in user_accounts_service.get_all_user_accounts():
        if (
            form_data.username == account.username
            and form_data.password == account.password
        ):
            user = User(
                username=form_data.username,
                password=form_data.password,
                role=account.role,
                remote_host=request.client.host,
            )
            users_service.add_user(user)

            # The /api/login endpoint returns a JSON web token response following the
            # specific structure dictated by the OAuth2 specification.
            return JSONWebTokenModel(**user.json_web_token.to_json())
    # This is the only api endpoint that does not require a token and hence will not by
    # default automatically return an empty 401 to unauthenticated requests. Therefore,
    # we need to manually return an empty 401 on unsuccessful login to prevent C2 server
    # fingerprinting.
    return Response(status_code=401)
