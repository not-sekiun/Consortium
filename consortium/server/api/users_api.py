from typing import Annotated

from fastapi import APIRouter, Depends

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerErrorError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.api_exceptions.users_api_exceptions import (
    UserNotFoundError as UserNotFoundAPIError,
)
from consortium.server.exceptions.service_exceptions.users_service_exceptions import (
    UserNotFoundError as UserNotFoundServiceError,
)
from consortium.server.models.user_models import UserModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest, get_current_user

users_service = server_singletons.users_service
router = APIRouter(
    prefix="/api/users",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerErrorError().to_pydantic_model()},
    },
    tags=["Users API"],
)


@router.get("/me", responses={200: {"model": UserModel}})
async def get_own_user(
    user: Annotated[UserModel, Depends(get_current_user)],
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
    return [UserModel(**user.to_json()) for user in users_service.get_all_users()]


@router.get(
    "/{user_id}",
    responses={
        200: {"model": UserModel},
        404: {
            "model": UserNotFoundAPIError.from_service_exception(
                service_exception=UserNotFoundServiceError(),
            ).to_pydantic_model(),
        },
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def get_user_by_user_id(
    user_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_USER_BY_USER_ID)),
    ],
) -> UserModel:
    try:
        user = users_service.get_user_by_user_id(user_id)
    except UserNotFoundServiceError as exc:
        raise UserNotFoundAPIError.from_service_exception(
            service_exception=exc,
        )

    return UserModel(**user.to_json())


async def update_user_display_name_by_user_id(
    display_name: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_USER_BY_USER_ID)),
    ],
) -> UserModel:
    try:
        user = users_service.update_user_display_name_by_user_id(
            display_name=display_name,
        )
    except UserNotFoundServiceError as exc:
        raise UserNotFoundAPIError.from_service_exception(
            service_exception=exc,
        )
    except EmptyUserDisplayNameServiceError as exc:
        raise EmptyUserDisplayNameAPIError.from_serivce_exception(
            service_exception=exc,
        )

    return UserModel(**user.to_json())
