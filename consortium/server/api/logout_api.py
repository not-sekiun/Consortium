from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import UUID4

import consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions
import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions import (
    user_accounts_api_exceptions as user_accounts_api_excs,
    users_api_exceptions as users_api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    InternalServerError,
    MethodNotAllowedError,
)
from consortium.server.exceptions.api_exceptions.pydantic_validation_api_exceptions import (
    InvalidUUIDError,
)
from consortium.server.exceptions.service_exceptions import (
    users_service_exceptions as users_consortium_excs,
)
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import (
    AuthorizeUserRequest,
    UserPermissions,
    get_current_user,
)

router = APIRouter(
    prefix="/api/logout",
    responses={
        401: {"description": "Unauthorized"},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Logout API"],
)

_users_service = server_singletons.users_service
_user_accounts_service = server_singletons.user_accounts_service

_user_account_not_found_error = user_accounts_api_excs.UserAccountNotFoundError(
    user_account_id="<user_account_id>"
)
_user_not_found_error = users_api_excs.UserNotFoundError(user_id="<user_id>")
_invalid_user_account_uuid_error = InvalidUUIDError(
    resource_name="user account", uuid_value="<uuid_value>"
)
_invalid_user_uuid_error = InvalidUUIDError(
    resource_name="user", uuid_value="<uuid_value>"
)


@router.post("", responses={204: {}}, status_code=204)
async def logout_from_server(
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    _users_service.logout_user_by_user_id(user_id=user.user_id)


@router.post(
    "/user-account/{user_account_id}",
    responses={
        204: {},
        404: {"model": _user_account_not_found_error.to_pydantic_model()},
        422: {"model": _invalid_user_account_uuid_error.to_pydantic_model()},
    },
    status_code=204,
)
async def logout_user_account_by_user_account_id(
    user_account_id: UUID4,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.LOGOUT_USER_ACCOUNT_BY_USER_ACCOUNT_ID)
        ),
    ],
) -> None:
    try:
        _user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=str(user_account_id)
        )
    except consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountIDNotFoundError:
        raise user_accounts_api_excs.UserAccountNotFoundError(
            user_account_id=str(user_account_id)
        ) from None

    for user in _users_service.get_all_users():
        if str(user.user_account.user_account_id) == str(user_account_id):
            _users_service.logout_user_by_user_id(user_id=user.user_id)


@router.post(
    "/user/{user_id}",
    responses={
        204: {},
        404: {"model": _user_not_found_error.to_pydantic_model()},
        422: {"model": _invalid_user_uuid_error.to_pydantic_model()},
    },
    status_code=204,
)
async def logout_user_by_user_id(
    user_id: UUID4,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.LOGOUT_USER_BY_USER_ID)),
    ],
) -> None:
    try:
        _users_service.logout_user_by_user_id(user_id=str(user_id))
    except users_consortium_excs.UserIDNotFoundError:
        raise users_api_excs.UserNotFoundError(user_id=str(user_id)) from None
