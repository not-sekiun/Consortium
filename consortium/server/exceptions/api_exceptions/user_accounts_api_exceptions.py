from consortium.server.exceptions.api_exceptions.http_exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnprocessableEntityError,
)


# The user accounts service distinguishes between not finding a user account by its
# user account ID or username. Therefore, we have separate service exceptions for each
# case. However, the API layer only exposes a single `UserAccountNotFoundError` because
# operations for accessing user accounts only can occur through the ID.
class UserAccountNotFoundError(NotFoundError):
    code = "USER_ACCOUNT_NOT_FOUND_ERROR"

    def __init__(self, user_account_id: str):
        super().__init__(
            f"Failed to find the requested user account. No user account was found "
            f"with the provided user account ID '{user_account_id}'.",
        )


class EmptyUserAccountUsernameError(UnprocessableEntityError): ...


class EmptyUserAccountPasswordError(UnprocessableEntityError): ...


class InvalidUserAccountRoleError(UnprocessableEntityError): ...


class UserAccountUsernameAlreadyExistsError(ConflictError): ...


# Add a bit more context in the error message compared to the services error message.
class UserAccountAuthenticationError(ForbiddenError):
    code = "USER_ACCOUNT_AUTHENTICATION_ERROR"

    def __init__(self):
        super().__init__(
            "Failed to authenticate the user account while performing the requested "
            "operation. Invalid credentials were provided.",
        )
