from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import ForbiddenError
from consortium.server.exceptions.consortium_exceptions.users_consortium_exceptions import (
    UserAccessTokenNotFoundError,
)
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.objects.user_objects import User
from consortium.server.server_jwt_config import (
    JSON_WEB_TOKEN_ALGORITHMS,
    JSON_WEB_TOKEN_SECRET_KEY,
)

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
_users_service = server_singletons.users_service
_authorization_service = server_singletons.authorization_service


# Ordinarily we would use the middleware to check if the user is logged in, but
# specifically for requests to /api/login we need to manually check if the user is
# already authenticated and return an actual error response if they are. We also need to
# take specific action depending on whether the user is logged in or not, hence the
# returning of a boolean over the raising of ForbiddenError.
def is_user_logged_in(
    request: Request,
) -> bool:
    # Since /api/login is the only API  endpoint that does not require a value, neither
    # our middleware nor our authorization dependencies will guarantee the identity of
    # the requester. Therefore, in this API endpoint specifically we need to manually
    # check if the user is already authenticated and return an actual error response.
    try:
        # if the Authorization header is not present, KeyError is thrown. The header
        # is in lowercase within the headers dictionary of the request object
        auth_header = request.headers["authorization"]
        if not auth_header.startswith("Bearer "):
            return False
        # format of the Authorization header is: Bearer <value>
        encoded_json_web_token = auth_header[7:]
        decoded_json_web_token = jwt.decode(
            jwt=encoded_json_web_token,
            key=JSON_WEB_TOKEN_SECRET_KEY,
            algorithms=JSON_WEB_TOKEN_ALGORITHMS,
        )
        access_token = decoded_json_web_token["sub"]
        # check if the user exists in the users service, ie if they are logged in or
        # not. If they are not logged in, this call raises a ValueError
        _ = _users_service.get_user_by_access_token(access_token)
        return True
    # `KeyError`: Authorization header is not present
    # `IndexError`: Authorization header is empty
    # `ValueError`: User does not exist in the users service
    # `jwt.exceptions.InvalidTokenError`: JSON Web Token is invalid, base exception
    # for any failure on the decode call for a value
    # `UserAccessTokenNotFoundError`: Valid JSON Web Token but does not exist in the
    # current set of users
    except (
        KeyError,
        IndexError,
        ValueError,
        jwt.exceptions.InvalidTokenError,
        UserAccessTokenNotFoundError,
    ):
        return False


def get_current_user(
    encoded_json_web_token: Annotated[str, Depends(_oauth2_scheme)],
) -> User:
    # The middleware has already checked if the JSON Web Token is valid ahead of time,
    # so we can safely decode it here without error handling.
    decoded_json_web_token = jwt.decode(
        jwt=encoded_json_web_token,
        key=JSON_WEB_TOKEN_SECRET_KEY,
        algorithms=JSON_WEB_TOKEN_ALGORITHMS,
    )
    access_token = decoded_json_web_token["sub"]
    # The middleware has already checked that the access value is valid ahead of time,
    # so we can safely use it here without error handling.
    return _users_service.get_user_by_access_token(access_token)


class AuthorizeUserRequest:
    def __init__(self, user_permission: UserPermissions):
        self._user_permission = user_permission

    def __call__(
        self,
        user: Annotated[User, Depends(get_current_user)],
    ) -> None:
        if not _authorization_service.has_permission(user.role, self._user_permission):
            raise ForbiddenError
