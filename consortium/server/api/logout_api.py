from typing import Annotated

from fastapi import APIRouter, Depends

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    InternalServerErrorError,
    MethodNotAllowedError,
    UnauthorizedError,
)
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import get_current_user

users_service = server_singletons.users_service
router = APIRouter(
    prefix="/api/logout",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerErrorError().to_pydantic_model()},
    },
    tags=["Logout API"],
)


@router.post("", responses={200: {"model": SuccessResponseModel}})
async def logout_from_server(
    user: Annotated[User, Depends(get_current_user)],
) -> SuccessResponseModel:
    users_service.logout_user_by_user_id(user_id=user.user_id)
    return SuccessResponseModel()
