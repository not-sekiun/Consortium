from typing import Annotated

from fastapi import APIRouter, Depends

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
)
from consortium.server.models.server_models import ReleaseModel, ServerConfigModel
from consortium.server.objects.user_account_objects import UserPermissions
from consortium.server.server_dependencies import AuthorizeUserRequest

router = APIRouter(
    prefix="/api/server",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        403: {"model": ForbiddenError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
    tags=["Server API"],
)

_server = server_singletons.server
_release_service = server_singletons.release_service


@router.get(
    "/release",
    responses={
        200: {"model": ReleaseModel},
    },
)
async def get_server_release(
    _: Annotated[
        None,
        Depends(AuthorizeUserRequest(UserPermissions.READ_SERVER_RELEASE)),
    ],
) -> ReleaseModel:
    return _release_service.release


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
