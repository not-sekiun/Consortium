from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

import consortium.server.server_singletons as server_singletons
from consortium.server.models.common_models import SuccessResponseModel
from consortium.server.objects.user_objects import User
from consortium.server.server_dependencies import get_current_user
from consortium.server.server_exceptions import (
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
)

router = APIRouter(
    prefix="/api/logout",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
users_service = server_singletons.users_service


@router.post("", responses={200: {"model": SuccessResponseModel}})
async def logout_from_server(
    user: Annotated[User, Depends(get_current_user)],
) -> SuccessResponseModel:
    users_service.remove_user(user)
    return SuccessResponseModel()
