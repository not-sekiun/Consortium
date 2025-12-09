"""
Exception hierarchy for the users service:

- BaseServiceException: Base class for all service-related exceptions.
 - UsersServiceError: Base class for all users service exceptions.
   - UserNotFoundError: User not found.
     - UserIDNotFoundError: User with provided ID not found.
     - UserAccessTokenNotFoundError: User with provided access token not found.
   -
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class UsersServiceError(BaseServiceException):
    code = "USERS_SERVICE_ERROR"


class UserNotFoundError(UsersServiceError):
    code = "USER_NOT_FOUND_ERROR"


class UserIDNotFoundError(UserNotFoundError):
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
        )


class UserAccessTokenNotFoundError(UserNotFoundError):
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
        )


class EmptyUserDisplayNameError(UsersServiceError):
    code = "EMPTY_USER_DISPLAY_NAME_ERROR"

    def __init__(
        self,
        user_str: str,
    ):
        super().__init__(
            message=(
                f"Failed to update the display name for user '{user_str}'. Display "
                f"name cannot be empty."
            ),
        )


class IdenticalUserDisplayNameError(UsersServiceError):
    code = "IDENTICAL_USER_DISPLAY_NAME_ERROR"

    def __init__(
        self,
        user_str: str,
        display_name: str,
    ):
        super().__init__(
            message=(
                f"Failed to update the display name for user '{user_str}'. Display "
                f"name '{display_name}' is identical to the currently used display "
                f"name."
            ),
        )
