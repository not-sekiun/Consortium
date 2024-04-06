from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.models.server_models import ServerConfigModel, ServerReleaseModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_config import SERVER_RELEASE
from consortium.server.server_dependencies import AuthorizeUserRequest
from consortium.server.server_exceptions import (
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
)

router = APIRouter(
    prefix="/api/server",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


@router.get(
    "/release",
    responses={
        200: {"model": ServerReleaseModel},
    },
)
async def get_server_release(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_SERVER_RELEASE)),
    ],
) -> ServerReleaseModel:
    return SERVER_RELEASE


@router.get(
    "/config",
    responses={
        200: {"model": ServerConfigModel},
    },
)
async def get_server_config(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_SERVER_CONFIG)),
    ],
) -> ServerConfigModel:
    return server_singletons.server.server_config
