# Errors for the api endpoint /api/login.
# - AlreadyLoggedInError
from typing import Any

from consortium.server.exceptions.base_server_exception import BaseServerException


class AlreadyLoggedInError(BaseServerException):
    def __init__(
        self,
        message: str = "The user is already logged in.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=409,
            code="ALREADY_LOGGED_IN_ERROR",
            message=message,
            detail=detail,
        )
