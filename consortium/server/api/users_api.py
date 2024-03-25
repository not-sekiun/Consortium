from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.models.user_models import UserModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest, get_current_user
from consortium.server.server_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
    UnprocessableEntityError,
    UserNotFoundError,
)

router = APIRouter(
    prefix="/api/users",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
users_service = server_singletons.users_service


@router.get("/me", responses={200: {"model": UserModel}})
async def get_own_user_info(
    user: Annotated[UserModel, Depends(get_current_user)],
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_OWN_USER_INFO)),
    ],
) -> UserModel:
    return UserModel(**user.to_json())


@router.get(
    "/all",
    responses={
        200: {"model": list[UserModel]},
        403: {"model": ForbiddenError().to_pydantic_model()},
    },
)
async def get_all_users_info(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_ALL_USERS_INFO)),
    ],
) -> list[UserModel]:
    return [UserModel(**user.to_json()) for user in users_service.get_all_users()]


@router.get(
    "/{user_id}",
    responses={
        200: {"model": UserModel},
        403: {"model": ForbiddenError().to_pydantic_model()},
        404: {"model": UserNotFoundError().to_pydantic_model()},
        422: {
            "model": UnprocessableEntityError(
                detail=[{"loc": ["string", 0], "msg": "string", "type": "string"}],
            ).to_pydantic_model(),
        },
    },
)
async def get_user_info_by_user_id(
    user_id: str,
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_USER_INFO_BY_USER_ID)),
    ],
) -> UserModel:
    try:
        user = users_service.get_user_by_user_id(user_id)
        return UserModel(**user.to_json())
    except ValueError:
        raise UserNotFoundError
