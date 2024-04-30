# Errors for the api endpoint /api/user-accounts.
# - HTTPError
#   - NotFoundError
#     - UserAccountNotFoundError
#   - UnprocessableEntityError
#     - UserAccountModificationError
#       - IdenticalUserAccountUsernameError
#       - UserAccountUsernameAlreadyExistsError
#       - IdenticalUserAccountPasswordError
#       - EmptyUserAccountPasswordError
#       - IdenticalUserAccountRoleError
from typing import Any

from consortium.server.exceptions.http_exceptions import (
    NotFoundError,
    UnprocessableEntityError,
)
from consortium.server.objects.user_account_objects import UserRole


class UserAccountNotFoundError(NotFoundError):
    def __init__(
        self,
        user_account_id: str | None,
    ) -> None:
        # user_account_id is None in the specific case when a logged-in user makes a
        # GET request to /api/user-accounts/me and the user account is not found
        # because it was deleted.
        if user_account_id is None:
            message = "The requested user account was not found."
        else:
            message = (
                "The requested user account with the provided user account ID "
                f'"{user_account_id}" was not found.'
            )

        super().__init__(
            status_code=404,
            code="USER_ACCOUNT_NOT_FOUND_ERROR",
            message=message,
            detail={"user_account_id": user_account_id},
        )


class UserAccountModificationError(UnprocessableEntityError):
    def __init__(
        self,
        status_code: int = 422,
        code: str = "USER_ACCOUNT_MODIFICATION_ERROR",
        message: str = "An error occurred while attempting to modify the user account.",
        detail: Any = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            code=code,
            message=message,
            detail=detail,
        )


class IdenticalUserAccountUsernameError(UserAccountModificationError):
    def __init__(
        self,
        username: str,
    ) -> None:
        super().__init__(
            status_code=422,
            code="IDENTICAL_USER_ACCOUNT_USERNAME_ERROR",
            message=f'The provided username "{username}" is identical to the currently '
            "used username for the user account.",
            detail={"username": username},
        )


class UserAccountUsernameAlreadyExistsError(UserAccountModificationError):
    def __init__(
        self,
        username: str,
    ) -> None:
        super().__init__(
            status_code=422,
            code="USER_ACCOUNT_USERNAME_ALREADY_EXISTS_ERROR",
            message=(
                f'The provided username "{username}" is already in use by another user '
                "account."
            ),
            detail={"username": username},
        )


class IdenticalUserAccountPasswordError(UserAccountModificationError):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            status_code=422,
            code="IDENTICAL_USER_ACCOUNT_PASSWORD_ERROR",
            message=(
                "The provided password is identical to the currently used password for "
                "the user account."
            ),
            detail=None,
        )


class EmptyUserAccountPasswordError(UserAccountModificationError):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            status_code=422,
            code="EMPTY_USER_ACCOUNT_PASSWORD_ERROR",
            message="The provided password cannot be empty.",
            detail=None,
        )


class IdenticalUserAccountRoleError(UserAccountModificationError):
    def __init__(
        self,
        role: UserRole,
    ) -> None:
        super().__init__(
            status_code=422,
            code="IDENTICAL_USER_ACCOUNT_ROLE_ERROR",
            message=(
                f'The provided role "{role}" is identical to the current role of the '
                "user account."
            ),
            detail={"role": role},
        )
