"""Exception hierarchy:

- [`BaseConsortiumError`][consortium.server.exceptions.consortium_exceptions.base_consortium_exception.BaseConsortiumError]
    - [`UsersError`][consortium.server.exceptions.consortium_exceptions.users_consortium_exceptions.UsersError]
        - [`UsersServiceError`][consortium.server.exceptions.consortium_exceptions.users_consortium_exceptions.UsersServiceError]
            - [`UserNotFoundError`][consortium.server.exceptions.consortium_exceptions.users_consortium_exceptions.UserNotFoundError]
                - [`UserIDNotFoundError`][consortium.server.exceptions.consortium_exceptions.users_consortium_exceptions.UserIDNotFoundError]
                - [`UserAccessTokenNotFoundError`][consortium.server.exceptions.consortium_exceptions.users_consortium_exceptions.UserAccessTokenNotFoundError]
"""

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


class UsersError(BaseConsortiumError):
    """Base exception for all users related errors."""

    code = "USERS_ERROR"


class UsersServiceError(UsersError):
    """Base exception for all users service related errors."""

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
    """Raised when the requested user with the provided user access value was not found in
    the users service
    """

    code = "USER_ACCESS_TOKEN_NOT_FOUND_ERROR"

    def __init__(
        self,
        access_token: str,
    ):
        super().__init__(
            message=(
                "Failed to find the requested user. No user found with the provided "
                f"access value '{access_token}'."
            ),
            detail={"access_token": access_token},
        )
