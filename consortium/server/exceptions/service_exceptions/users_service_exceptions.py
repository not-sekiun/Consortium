"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`UsersServiceError`][consortium.server.exceptions.service_exceptions.users_service_exceptions.UsersServiceError]
        - [`UserNotFoundError`][consortium.server.exceptions.service_exceptions.users_service_exceptions.UserNotFoundError]
            - [`UserIDNotFoundError`][consortium.server.exceptions.service_exceptions.users_service_exceptions.UserIDNotFoundError]
            - [`UserAccessTokenNotFoundError`][consortium.server.exceptions.service_exceptions.users_service_exceptions.UserAccessTokenNotFoundError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class UsersServiceError(BaseServiceError):
    """Base exception for all errors that occur within the users service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

    code = "USERS_SERVICE_ERROR"


class UserNotFoundError(UsersServiceError):
    """Raised when the requested user was not found in the users service."""

    code = "USER_NOT_FOUND_ERROR"


class UserIDNotFoundError(UserNotFoundError):
    """Raised when the requested user with the provided user ID was not found in the users
    service
    """

    code = "USER_ID_NOT_FOUND_ERROR"

    def __init__(
        self,
        user_id: str,
    ):
        super().__init__(
            message=(
                "Failed to find the requested user. No user could be found with the "
                f"provided user ID '{user_id}'."
            ),
            detail={"user_id": user_id},
        )


class UserAccessTokenNotFoundError(UserNotFoundError):
    """Raised when the requested user with the provided user access token was not found
    in the users service
    """

    code = "USER_ACCESS_TOKEN_NOT_FOUND_ERROR"

    def __init__(
        self,
        access_token: str,
    ):
        super().__init__(
            message=(
                "Failed to find the requested user. No user found with the provided "
                f"access token '{access_token}'."
            ),
            detail={"access_token": access_token},
        )
