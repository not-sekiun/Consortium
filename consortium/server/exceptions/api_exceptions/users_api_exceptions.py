# Errors for the api endpoint /api/users.
# - HTTPError
#   - NotFoundError
#     - UserNotFoundAPIError
from consortium.server.exceptions.api_exceptions.http_exceptions import (
    NotFoundHTTPError,
)


class UserNotFoundAPIError(NotFoundHTTPError):
    def __init__(
        self,
        user_id: str,
    ) -> None:
        super().__init__(
            status_code=404,
            code="USER_NOT_FOUND_ERROR",
            message=(
                f"The requested user with the provided user ID '{user_id}' was not "
                "found."
            ),
        )
