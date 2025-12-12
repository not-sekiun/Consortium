from typing import Annotated

from fastapi import APIRouter, Depends

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions import (
    user_accounts_api_exceptions as user_accounts_api_excs,
    users_api_exceptions as users_api_excs,
)
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
)
from consortium.server.exceptions.service_exceptions import (
    user_accounts_service_exceptions as user_accounts_svc_excs,
    users_service_exceptions as users_svc_excs,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import (
    AuthorizeUserRequest,
    UserPermissions,
    get_current_user,
)

router = APIRouter(
    prefix="/api/logout",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Logout API"],
)

users_service = server_singletons.users_service
user_accounts_service = server_singletons.user_accounts_service

_user_account_not_found_error = user_accounts_api_excs.UserAccountNotFoundError(
    user_account_id="<user_account_id>"
)
_user_not_found_error = users_api_excs.UserNotFoundError(user_id="<user_id>")


@router.post("", responses={200: {"model": SuccessResponseModel}})
async def logout_from_server(
    user: Annotated[User, Depends(get_current_user)],
) -> SuccessResponseModel:
    users_service.logout_user_by_user_id(user_id=user.user_id)
    return SuccessResponseModel()


@router.post(
    "/user-account/{user_account_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {"model": _user_account_not_found_error.to_pydantic_model()},
    },
)
async def logout_user_account_by_user_account_id(
    user_account_id: str,
    _: Annotated[
        None,
        Depends(
            AuthorizeUserRequest(UserPermissions.LOGOUT_USER_ACCOUNT_BY_USER_ACCOUNT_ID)
        ),
    ],
) -> SuccessResponseModel:
    try:
        user_accounts_service.get_user_account_by_user_account_id(
            user_account_id=user_account_id
        )
    except user_accounts_svc_excs.UserAccountIDNotFoundError:
        raise user_accounts_api_excs.UserAccountNotFoundError(
            user_account_id=user_account_id
        ) from None

    for user in users_service.get_all_users():
        if str(user.user_account.user_account_id) == user_account_id:
            users_service.logout_user_by_user_id(user_id=user.user_id)

    return SuccessResponseModel()


@router.post(
    "/user/{user_id}",
    responses={
        200: {"model": SuccessResponseModel},
        404: {"model": _user_not_found_error.to_pydantic_model()},
    },
)
async def logout_user_by_user_id(
    user_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.LOGOUT_USER_BY_USER_ID)),
    ],
) -> SuccessResponseModel:
    try:
        users_service.logout_user_by_user_id(user_id=user_id)
    except users_svc_excs.UserIDNotFoundError:
        raise users_api_excs.UserNotFoundError(user_id=user_id) from None

    return SuccessResponseModel()
