"""
Exception hierarchy for the users service.

- BaseServiceException: Base class for all service-related exceptions
  - UsersServiceError: Base class for all exceptions related to the users service.
    - UserNotFoundServiceError: Raised when a requested user is not found.
      - InvalidUserIDServiceError: Raised when the provided user ID is not found.
      - InvalidAccessTokenServiceError: Raised when a user could not be found with the provided access token.
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class UsersServiceError(BaseServiceException):
    def __init__(
        self,
        message: str = "An unexpected error occurred within the users service.",
    ):
        super().__init__(message=message)


class UserNotFoundServiceError(UsersServiceError):
    def __init__(
        self,
        message: str = "The requested user was not found within the users service",
    ):
        super().__init__(message=message)


class InvalidUserIDServiceError(UserNotFoundServiceError):
    def __init__(
        self,
        user_id: str,
        message: str | None = None,
    ):
        if message is None:
            message = f"No user found with the provided user ID: {user_id}"
        super().__init__(message=message)


class InvalidAccessTokenServiceError(UserNotFoundServiceError):
    def __init__(
        self,
        access_token: str,
        message: str | None = None,
    ):
        if message is None:
            message = f"No user found with the provided access token: {access_token}"
        super().__init__(message=message)
