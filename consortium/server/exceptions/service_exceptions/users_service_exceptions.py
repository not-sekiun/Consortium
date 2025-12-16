"""
Exception hierarchy for the users service.

- [BaseServiceException][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceException]
    - [UsersServiceError][consortium.server.exceptions.service_exceptions.users_service_exceptions.UsersServiceError]
        - [UserNotFoundError][consortium.server.exceptions.service_exceptions.users_service_exceptions.UserNotFoundError]
            - [UserIDNotFoundError][consortium.server.exceptions.service_exceptions.users_service_exceptions.UserIDNotFoundError]
            - [UserAccessTokenNotFoundError][consortium.server.exceptions.service_exceptions.users_service_exceptions.UserAccessTokenNotFoundError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)


class UsersServiceError(BaseServiceException):
    """
    Base exception for all users service errors.
    """

    code = "USERS_SERVICE_ERROR"


class UserNotFoundError(UsersServiceError):
    """
    Raised when a requested user could not be found.
    """

    code = "USER_NOT_FOUND_ERROR"


class UserIDNotFoundError(UserNotFoundError):
    """
    Raised when a user with the specified user ID could not be found.

    Args:
        user_id (str): The user ID that was not found.
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
    """
    Raised when a user with the specified access token could not be found.

    Args:
        access_token (str): The access token that was not found.
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
