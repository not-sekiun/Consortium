"""
Errors for the api endpoint /api/user-accounts:

- HTTPError
 - NotFoundError
   - UserAccountNotFoundError: User account with provided ID not found.
 - UnprocessableEntityError
   - IdenticalUserAccountUsernameError: New username identical to current username.
   - IdenticalUserAccountPasswordError: New password identical to current password.
   - IdenticalUserAccountRoleError: New role identical to current role.
   - EmptyUserAccountUsernameError: Provided username cannot be empty.
   - EmptyUserAccountPasswordError: Provided password cannot be empty.
   - InvalidUserAccountRoleError: Provided role is invalid.
   - UserAccountUsernameAlreadyExistsError: Provided username already in use.
 - ForbiddenError
   - UserAccountAuthenticationError: Provided user account credentials invalid.
"""

from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ForbiddenError,
    NotFoundError,
    UnprocessableEntityError,
)
from consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions import (
    EmptyUserAccountPasswordError as EmptyUserAccountPasswordServiceError,
    EmptyUserAccountUsernameError as EmptyUserAccountUsernameServiceError,
    IdenticalUserAccountPasswordError as IdenticalUserAccountPasswordServiceError,
    IdenticalUserAccountRoleError as IdenticalUserAccountRoleServiceError,
    IdenticalUserAccountUsernameError as IdenticalUserAccountUsernameServiceError,
    InvalidUserAccountRoleError as InvalidUserAccountRoleServiceError,
    UserAccountAuthenticationError as UserAccountAuthenticationServiceError,
    UserAccountIDNotFoundError,
    UserAccountUsernameAlreadyExistsError as UserAccountUsernameAlreadyExistsServiceError,
)
from consortium.server.objects.user_account_objects import UserRole


class UserAccountNotFoundError(NotFoundError):
    def __init__(
        self,
        user_account_id: str | None,
    ) -> None:
        # When the parameter `user_account_id` is `None` this means that the logged-in
        # user made a request to an endpoint identifying the user account as 'me'
        # (referencing the user account mapped to the currently logged-in user).
        if user_account_id is None:
            message = (
                "Failed to find the requested user account associated with the current "
                "user."
            )
        else:
            service_exception = UserAccountIDNotFoundError(
                user_account_id=user_account_id,
            )
            message = service_exception.message

        super().__init__(
            status_code=404,
            code="USER_ACCOUNT_NOT_FOUND_ERROR",
            message=message,
            detail=None,
        )


class IdenticalUserAccountUsernameError(UnprocessableEntityError):
    def __init__(
        self,
        username: str,
    ) -> None:
        service_exception = IdenticalUserAccountUsernameServiceError(username=username)
        super().__init__(
            status_code=422,
            code="IDENTICAL_USER_ACCOUNT_USERNAME_ERROR",
            message=service_exception.message,
        )


class IdenticalUserAccountPasswordError(UnprocessableEntityError):
    def __init__(
        self,
    ) -> None:
        service_exception = IdenticalUserAccountPasswordServiceError()
        super().__init__(
            status_code=422,
            code="IDENTICAL_USER_ACCOUNT_PASSWORD_ERROR",
            message=service_exception.message,
        )


class IdenticalUserAccountRoleError(UnprocessableEntityError):
    def __init__(
        self,
        role: UserRole,
    ) -> None:
        service_exception = IdenticalUserAccountRoleServiceError(role=role)
        super().__init__(
            status_code=422,
            code="IDENTICAL_USER_ACCOUNT_ROLE_ERROR",
            message=service_exception.message,
            detail=None,
        )


class EmptyUserAccountUsernameError(UnprocessableEntityError):
    def __init__(
        self,
    ) -> None:
        service_exception = EmptyUserAccountUsernameServiceError()
        super().__init__(
            status_code=422,
            code="EMPTY_USER_ACCOUNT_USERNAME_ERROR",
            message=service_exception.message,
        )


class EmptyUserAccountPasswordError(UnprocessableEntityError):
    def __init__(
        self,
    ) -> None:
        service_exception = EmptyUserAccountPasswordServiceError()
        super().__init__(
            status_code=422,
            code="EMPTY_USER_ACCOUNT_PASSWORD_ERROR",
            message=service_exception.message,
        )


class InvalidUserAccountRoleError(UnprocessableEntityError):
    def __init__(self, role: str) -> None:
        service_exception = InvalidUserAccountRoleServiceError(role=role)
        super().__init__(
            status_code=422,
            code="INVALID_USER_ACCOUNT_ROLE_ERROR",
            message=service_exception.message,
        )


class UserAccountUsernameAlreadyExistsError(UnprocessableEntityError):
    def __init__(
        self,
        username: str,
    ) -> None:
        service_exception = UserAccountUsernameAlreadyExistsServiceError(
            username=username,
        )
        super().__init__(
            status_code=422,
            code="USER_ACCOUNT_USERNAME_ALREADY_EXISTS_ERROR",
            message=service_exception.message,
        )


class UserAccountAuthenticationError(ForbiddenError):
    def __init__(self):
        service_exception = UserAccountAuthenticationServiceError()
        super().__init__(
            status_code=403,
            code="USER_ACCOUNT_AUTHENTICATION_ERROR",
            message=service_exception.message,
        )
