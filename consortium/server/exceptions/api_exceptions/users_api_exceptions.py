"""
Errors for the api endpoint /api/users:

- HTTPError
 - NotFoundError
   - UserNotFoundError: User with provided ID not found.
"""

from consortium.server.exceptions.api_exceptions.http_exceptions import NotFoundError
from consortium.server.exceptions.service_exceptions.users_service_exceptions import (
    UserIDNotFoundError,
)


class UserNotFoundError(NotFoundError):
    def __init__(
        self,
        user_id: str,
    ) -> None:
        exception = UserIDNotFoundError(user_id=user_id)
        super().__init__(
            status_code=404,
            code="USER_NOT_FOUND_ERROR",
            message=exception.message,
        )
