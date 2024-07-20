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


class UserAccountNotFoundError(NotFoundError):
    code = "USER_ACCOUNT_NOT_FOUND_ERROR"


class IdenticalUserAccountUsernameError(UnprocessableEntityError):
    code = "IDENTICAL_USER_ACCOUNT_USERNAME_ERROR"


class IdenticalUserAccountPasswordError(UnprocessableEntityError):
    code = "IDENTICAL_USER_ACCOUNT_PASSWORD_ERROR"


class IdenticalUserAccountRoleError(UnprocessableEntityError):
    code = "IDENTICAL_USER_ACCOUNT_ROLE_ERROR"


class EmptyUserAccountUsernameError(UnprocessableEntityError):
    code = "EMPTY_USER_ACCOUNT_USERNAME_ERROR"


class EmptyUserAccountPasswordError(UnprocessableEntityError):
    code = "EMPTY_USER_ACCOUNT_PASSWORD_ERROR"


class InvalidUserAccountRoleError(UnprocessableEntityError):
    code = "INVALID_USER_ACCOUNT_ROLE_ERROR"


class UserAccountUsernameAlreadyExistsError(UnprocessableEntityError):
    code = "USER_ACCOUNT_USERNAME_ALREADY_EXISTS_ERROR"


class UserAccountAuthenticationError(ForbiddenError):
    code = "USER_ACCOUNT_AUTHENTICATION_ERROR"
