from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import ForbiddenError
from consortium.server.exceptions.consortium_exceptions.users_consortium_exceptions import (
    UserAccessTokenNotFoundError,
)
from consortium.server.objects.user_account_objects import UserPermissions, UserRole
from consortium.server.objects.user_objects import User
from consortium.server.server_jwt_config import (
    JSON_WEB_TOKEN_ALGORITHMS,
    JSON_WEB_TOKEN_SECRET_KEY,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
users_service = server_singletons.users_service


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
        _ = users_service.get_user_by_access_token(access_token)
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
    encoded_json_web_token: Annotated[str, Depends(oauth2_scheme)],
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
    return users_service.get_user_by_access_token(access_token)


class AuthorizeUserRequest:
    ROLE_PERMISSIONS = {
        # All defined permissions now and in the future are granted to the admin
        UserRole.ADMIN: set(
            UserPermissions,
        ),
        # Operators have generally every permission except those that deal with user
        # accounts and user management
        UserRole.OPERATOR: {
            # Permissions for the /api/user-accounts endpoint
            UserPermissions.UPDATE_OWN_USER_ACCOUNT,
            UserPermissions.READ_OWN_USER_ACCOUNT,  # TODO: Probably should remove
            # Permissions for the /api/users endpoint
            UserPermissions.READ_OWN_USER,
            UserPermissions.READ_ALL_USERS,
            UserPermissions.READ_USER_BY_USER_ID,
            UserPermissions.UPDATE_OWN_USER,
            # Permissions for the /api/server endpoint
            UserPermissions.READ_SERVER_RELEASE,
            UserPermissions.READ_SERVER_CONFIG,
            # Permissions for the /api/listener-templates endpoint
            UserPermissions.CREATE_LISTENER,
            UserPermissions.READ_ALL_LISTENER_TEMPLATES,
            UserPermissions.READ_LISTENER_TEMPLATE_BY_LISTENER_TEMPLATE_ID,
            # Permissions for the /api/listeners endpoint
            UserPermissions.READ_ALL_LISTENERS,
            UserPermissions.READ_LISTENER_BY_LISTENER_ID,
            UserPermissions.START_LISTENER_BY_LISTENER_ID,
            UserPermissions.STOP_LISTENER_BY_LISTENER_ID,
            UserPermissions.CANCEL_LISTENER_BY_LISTENER_ID,
            UserPermissions.UPDATE_LISTENER_BY_LISTENER_ID,
            UserPermissions.DELETE_LISTENER_BY_LISTENER_ID,
            # Permissions for the /api/agent-templates endpoint
            UserPermissions.CREATE_AGENT_GENERATOR,
            UserPermissions.READ_ALL_AGENT_TEMPLATES,
            UserPermissions.READ_AGENT_TEMPLATE_BY_AGENT_TEMPLATE_ID,
            # Permissions for the /api/agent-generators endpoint
            UserPermissions.READ_ALL_AGENT_GENERATORS,
            UserPermissions.READ_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            UserPermissions.START_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            UserPermissions.STOP_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            UserPermissions.CANCEL_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            UserPermissions.UPDATE_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            UserPermissions.DELETE_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            # Permissions for the /api/agents endpoint
            UserPermissions.READ_ALL_AGENTS,
            UserPermissions.READ_AGENT_BY_AGENT_ID,
            UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID,
            UserPermissions.READ_AGENT_TASK_BY_AGENT_ID_AND_TASK_ID,
            UserPermissions.READ_ALL_AGENT_RESULTS_BY_AGENT_ID,
            UserPermissions.READ_AGENT_RESULT_BY_AGENT_ID_AND_TASK_ID_OR_RESULT_ID,
            UserPermissions.TASK_AGENT_BY_AGENT_ID,
            UserPermissions.UPDATE_AGENT_BY_AGENT_ID,
            # Permissions for the /api/events endpoint
            UserPermissions.USE_EVENTS_WEBSOCKET,
            # Permissions for the /api/assets endpoint
            UserPermissions.UPLOAD_ASSETS,
            UserPermissions.DOWNLOAD_ASSETS,
            UserPermissions.READ_ALL_ASSETS,
            UserPermissions.READ_ASSET_BY_ASSET_ID,
            UserPermissions.DELETE_ASSET_BY_ASSET_ID,
            # Permissions for the /api/artifacts endpoint
            UserPermissions.DOWNLOAD_ARTIFACTS,
            UserPermissions.READ_ALL_ARTIFACTS,
            UserPermissions.READ_ARTIFACT_BY_ARTIFACT_ID,
            UserPermissions.DELETE_ARTIFACT_BY_ARTIFACT_ID,
            # Permissions for the /api/payloads endpoint
            UserPermissions.DOWNLOAD_PAYLOADS,
            UserPermissions.READ_ALL_PAYLOADS,
            UserPermissions.READ_PAYLOAD_BY_PAYLOAD_ID,
            UserPermissions.DELETE_PAYLOAD_BY_PAYLOAD_ID,
        },
        # Spectators generally have only read-only permissions
        UserRole.SPECTATOR: {
            # Permissions for the /api/user-accounts endpoint
            UserPermissions.READ_OWN_USER_ACCOUNT,  # TODO: Probably should remove
            # Permissions for the /api/users endpoint
            UserPermissions.READ_OWN_USER,
            # The only non read permission, used to update display name
            UserPermissions.UPDATE_OWN_USER,
            # Permissions for the /api/server endpoint
            UserPermissions.READ_SERVER_RELEASE,
            # Permissions for the /api/listener-templates endpoint
            UserPermissions.READ_ALL_LISTENER_TEMPLATES,
            UserPermissions.READ_LISTENER_TEMPLATE_BY_LISTENER_TEMPLATE_ID,
            # Permissions for the /api/listeners endpoint
            UserPermissions.READ_ALL_LISTENERS,
            UserPermissions.READ_LISTENER_BY_LISTENER_ID,
            # Permissions for the /api/agent-templates endpoint
            UserPermissions.READ_ALL_AGENT_TEMPLATES,
            UserPermissions.READ_AGENT_TEMPLATE_BY_AGENT_TEMPLATE_ID,
            # Permissions for the /api/agent-generators endpoint
            UserPermissions.READ_ALL_AGENT_GENERATORS,
            UserPermissions.READ_AGENT_GENERATOR_BY_AGENT_GENERATOR_ID,
            # Permissions for the /api/agents endpoint
            UserPermissions.READ_ALL_AGENTS,
            UserPermissions.READ_AGENT_BY_AGENT_ID,
            UserPermissions.READ_ALL_AGENT_TASKS_BY_AGENT_ID,
            UserPermissions.READ_AGENT_TASK_BY_AGENT_ID_AND_TASK_ID,
            UserPermissions.READ_ALL_AGENT_RESULTS_BY_AGENT_ID,
            UserPermissions.READ_AGENT_RESULT_BY_AGENT_ID_AND_TASK_ID_OR_RESULT_ID,
            # Permissions for the /api/events endpoint
            UserPermissions.USE_EVENTS_WEBSOCKET,
            # Permissions for the /api/assets endpoint
            UserPermissions.READ_ALL_ASSETS,
            UserPermissions.READ_ASSET_BY_ASSET_ID,
            # Permissions for the /api/artifacts endpoint
            UserPermissions.READ_ALL_ARTIFACTS,
            UserPermissions.READ_ARTIFACT_BY_ARTIFACT_ID,
            # Permissions for the /api/payloads endpoint
            UserPermissions.READ_ALL_PAYLOADS,
            UserPermissions.READ_PAYLOAD_BY_PAYLOAD_ID,
        },
    }

    def __init__(self, user_permission: UserPermissions):
        self._user_permission = user_permission

    def __call__(
        self,
        user: Annotated[User, Depends(get_current_user)],
    ) -> None:
        if self._user_permission not in self.ROLE_PERMISSIONS[user.role]:
            raise ForbiddenError
