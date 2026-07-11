from typing import Annotated

from fastapi import APIRouter, Body, Depends
from pydantic import UUID4

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions import users_api_exceptions as api_excs
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.api_exceptions.pydantic_validation_api_exceptions import (
    InvalidUUIDError,
)
from consortium.server.exceptions.service_exceptions import (
    users_service_exceptions as consortium_excs,
)
from consortium.server.models.user_models import UserModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import AuthorizeUserRequest, get_current_user

router = APIRouter(
    prefix="/api/users",
    responses={
        401: {"description": "Unauthorized"},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Users API"],
)

_users_service = server_singletons.users_service

_user_not_found_error = api_excs.UserNotFoundError(user_id="<user_id>")
_unprocessable_entity_error = UnprocessableEntityError(
    detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}]
)
_invalid_uuid_error = InvalidUUIDError(resource_name="user", uuid_value="<uuid_value>")


@router.get("/me", responses={200: {"model": UserModel}})
async def get_own_user(
    user: Annotated[User, Depends(get_current_user)],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_OWN_USER)),
    ],
) -> UserModel:
    return UserModel(**user.to_json())


@router.get(
    "/all",
    responses={
        200: {"model": list[UserModel]},
    },
)
async def get_all_users(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_USERS)),
    ],
) -> list[UserModel]:
    return [UserModel(**user.to_json()) for user in _users_service.get_all_users()]


@router.get(
    "/{user_id}",
    responses={
        200: {"model": UserModel},
        404: {"model": _user_not_found_error.to_pydantic_model()},
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model(),
        },
    },
)
async def get_user_by_user_id(
    user_id: UUID4,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_USER_BY_USER_ID)),
    ],
) -> UserModel:
    try:
        user = _users_service.get_user_by_user_id(str(user_id))
    except consortium_excs.UserIDNotFoundError:
        raise api_excs.UserNotFoundError(
            user_id=str(user_id),
        ) from None

    return UserModel(**user.to_json())


@router.patch(
    "/me",
    responses={
        200: {"model": UserModel},
        404: {"model": _user_not_found_error.to_pydantic_model()},
    },
)
async def update_own_display_name(
    display_name: Annotated[str, Body(embed=True)],
    user: Annotated[User, Depends(get_current_user)],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.UPDATE_OWN_USER)),
    ],
) -> UserModel:
    try:
        updated_user = _users_service.update_user_display_name_by_user_id(
            user_id=str(user.user_id),
            display_name=display_name,
        )
    except consortium_excs.UserIDNotFoundError:
        # This should never happen since the user is updating their own display name
        raise api_excs.UserNotFoundError(
            user_id=str(user.user_id),
        ) from None

    return updated_user


@router.patch(
    "/{user_id}",
    responses={
        200: {"model": UserModel},
        404: {"model": _user_not_found_error.to_pydantic_model()},
        422: {
            "model": _invalid_uuid_error.to_pydantic_model()
            | _unprocessable_entity_error.to_pydantic_model(),
        },
    },
)
async def update_user_display_name_by_user_id(
    user_id: UUID4,
    display_name: Annotated[str, Body(embed=True)],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.UPDATE_USER_BY_USER_ID)),
    ],
) -> UserModel:
    try:
        user = _users_service.update_user_display_name_by_user_id(
            user_id=str(user_id),
            display_name=display_name,
        )
    except consortium_excs.UserIDNotFoundError:
        raise api_excs.UserNotFoundError(
            user_id=str(user_id),
        ) from None

    return UserModel(**user.to_json())
