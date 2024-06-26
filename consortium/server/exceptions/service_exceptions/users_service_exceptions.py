"""
Exception hierarchy for the users service:

- BaseServiceException: Base class for all service-related exceptions.
 - UsersServiceError: Base class for all users service exceptions.
   - UserNotFoundError: User not found.
     - UserIDNotFoundError: User with provided ID not found.
     - UserAccessTokenNotFoundError: User with provided access token not found.
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class UsersServiceError(BaseServiceException):
    def __init__(
        self,
        message: str = "An error occurred in the users service.",
    ):
        super().__init__(message=message)


class UserNotFoundError(UsersServiceError):
    def __init__(
        self,
        message: str = "Failed to find the requested user.",
    ):
        super().__init__(message=message)


class UserIDNotFoundError(UserNotFoundError):
    def __init__(
        self,
        user_id: str,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "Failed to find the requested user. No user could be found with the "
                f"provided user ID '{user_id}'."
            )
        super().__init__(message=message)


class UserAccessTokenNotFoundError(UserNotFoundError):
    def __init__(
        self,
        access_token: str,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "Failed to find the requested user. No user found with the provided "
                f"access token '{access_token}'."
            )
        super().__init__(message=message)
