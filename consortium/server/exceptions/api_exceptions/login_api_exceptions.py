"""
Errors for the api endpoint /api/login:

- ConflictError: The request could not be completed due to a conflict with the current
state of the resource.
  - AlreadyLoggedInError: User is already logged in.
"""

from consortium.server.exceptions.api_exceptions.http_exceptions import ConflictError


class AlreadyLoggedInError(ConflictError):
    code = "ALREADY_LOGGED_IN_ERROR"

    def __init__(
        self,
    ) -> None:
        super().__init__(
            message=(
                "Failed to authenticate user. The current user is already logged in."
            ),
        )
