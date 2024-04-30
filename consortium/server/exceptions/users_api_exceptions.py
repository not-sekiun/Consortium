# Errors for the api endpoint /api/users.
# - HTTPError
#   - NotFoundError
#     - UserNotFoundError
from consortium.server.exceptions.http_exceptions import NotFoundError


class UserNotFoundError(NotFoundError):
    def __init__(
        self,
        user_id: str,
    ) -> None:
        super().__init__(
            status_code=404,
            code="USER_NOT_FOUND_ERROR",
            message=f'The requested user with the provided user ID "{user_id}" was not '
            "found.",
            detail={"user_id": user_id},
        )
