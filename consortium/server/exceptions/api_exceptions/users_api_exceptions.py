from consortium.server.exceptions.api_exceptions.http_exceptions import (
    NotFoundError,
)


# The users service distinguishes between not finding a user by its user ID or
# access token. Therefore, we have separate exceptions for each case.
# However the API layer only exposes a single `UserNotFoundError`.
class UserNotFoundError(NotFoundError):
    code = "USER_NOT_FOUND_ERROR"

    def __init__(self, user_id: str):
        super().__init__(
            message=(
                f"Failed to find the requested user. No user was found with the "
                f"provided user ID '{user_id}'."
            ),
        )
