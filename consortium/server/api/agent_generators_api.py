from fastapi import APIRouter
from fastapi.security import OAuth2PasswordBearer

from consortium.server.server_exceptions import (
    InternalServerError,
    MethodNotAllowedError,
    UnauthorizedError,
)

router = APIRouter(
    prefix="/api/agent-generators",
    responses={
        401: {"model": UnauthorizedError().to_pydantic_model()},
        405: {"model": MethodNotAllowedError().to_pydantic_model()},
        500: {"model": InternalServerError().to_pydantic_model()},
    },
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
