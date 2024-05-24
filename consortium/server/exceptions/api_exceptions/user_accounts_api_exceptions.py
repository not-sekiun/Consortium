# Errors for the api endpoint /api/user-accounts.
# - HTTPError
#   - NotFoundError
#     - UserAccountNotFoundAPIError
#   - UnprocessableEntityError
#     - UserAccountManagementAPIError
#       - IdenticalUserAccountUsernameAPIError
#       - IdenticalUserAccountPasswordAPIError
#       - IdenticalUserAccountRoleAPIError
#       - EmptyUserAccountUsernameAPIError
#       - EmptyUserAccountPasswordAPIError
#       - InvalidUserAccountRoleAPIError
#       - UserAccountUsernameAlreadyExistsAPIError
#   - ForbiddenHTTPError
#       - InvalidUserAccountCredentials
from typing import Any

from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenHTTPError,
    NotFoundHTTPError,
    UnprocessableEntityHTTPError,
)
from consortium.server.objects.user_account_objects import UserRole


class UserAccountNotFoundAPIError(NotFoundHTTPError):
    def __init__(
        self,
        user_account_id: str | None,
    ) -> None:
        # When the parameter `user_account_id` is `None` this means that the logged-in
        # user made a request to an endpoint identifying the user account as 'me'
        # (referencing the user account mapped to the currently logged-in user).
        if user_account_id is None:
            message = (
                "The requested user account associated with the current user was not "
                "found."
            )
        else:
            message = (
                "The requested user account with the provided user account ID "
                f"'{user_account_id}' was not found."
            )

        super().__init__(
            status_code=404,
            code="USER_ACCOUNT_NOT_FOUND_ERROR",
            message=message,
            detail=None,
        )


class UserAccountManagementAPIError(UnprocessableEntityHTTPError):
    def __init__(
        self,
        status_code: int = 422,
        code: str = "USER_ACCOUNT_MODIFICATION_ERROR",
        message: str = "An error occurred while managing the user account.",
        detail: Any | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class IdenticalUserAccountUsernameAPIError(UserAccountManagementAPIError):
    def __init__(
        self,
        username: str,
    ) -> None:
        super().__init__(
            status_code=422,
            code="IDENTICAL_USER_ACCOUNT_USERNAME_ERROR",
            message=(
                f"The provided username '{username}' is identical to the currently "
                f"used username for the user account."
            ),
            detail=None,
        )


class IdenticalUserAccountPasswordAPIError(UserAccountManagementAPIError):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            status_code=422,
            code="IDENTICAL_USER_ACCOUNT_PASSWORD_ERROR",
            message=(
                "The provided user account password is identical to the currently used "
                "password for the user account."
            ),
            detail=None,
        )


class IdenticalUserAccountRoleAPIError(UserAccountManagementAPIError):
    def __init__(
        self,
        role: UserRole,
    ) -> None:
        super().__init__(
            status_code=422,
            code="IDENTICAL_USER_ACCOUNT_ROLE_ERROR",
            message=(
                f"The provided user account role '{role}' is identical to the current "
                "role of the user account."
            ),
            detail=None,
        )


class EmptyUserAccountUsernameAPIError(UserAccountManagementAPIError):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            status_code=422,
            code="EMPTY_USER_ACCOUNT_USERNAME_ERROR",
            message="The provided user account username cannot be empty.",
            detail=None,
        )


class EmptyUserAccountPasswordAPIError(UserAccountManagementAPIError):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            status_code=422,
            code="EMPTY_USER_ACCOUNT_PASSWORD_ERROR",
            message="The provided user account password cannot be empty.",
            detail=None,
        )


class InvalidUserAccountRoleAPIError(UserAccountManagementAPIError):
    def __init__(self, role: str) -> None:
        super().__init__(
            status_code=422,
            code="INVALID_USER_ACCOUNT_ROLE_ERROR",
            message=f"The provided user account role '{role}' is invalid.",
            detail=None,
        )


class UserAccountUsernameAlreadyExistsAPIError(UserAccountManagementAPIError):
    def __init__(
        self,
        username: str,
    ) -> None:
        super().__init__(
            status_code=422,
            code="USER_ACCOUNT_USERNAME_ALREADY_EXISTS_ERROR",
            message=(
                f"The provided user account username '{username}' is already in use by "
                "another user account."
            ),
            detail=None,
        )


class InvalidUserAccountCredentials(ForbiddenHTTPError):
    def __init__(self):
        super().__init__(
            status_code=403,
            code="INVALID_USER_ACCOUNT_CREDENTIALS",
            message="The provided user account credentials were invalid.",
            detail=None,
        )
