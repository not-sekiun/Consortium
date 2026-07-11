"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`UserAccountsServiceError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsServiceError]
        - [`UserAccountNotFoundError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountNotFoundError]
            - [`UserAccountIDNotFoundError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountIDNotFoundError]
            - [`UserAccountUsernameNotFoundError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountUsernameNotFoundError]
        - [`UserAccountsFileError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileError]
            - [`UserAccountsFileNotFoundError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileNotFoundError]
            - [`UserAccountsFileAccessError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileAccessError]
                - [`UserAccountsFileReadAccessError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileReadAccessError]
                - [`UserAccountsFileWriteAccessError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileWriteAccessError]
            - [`UserAccountsFilepathIsDirectoryError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFilepathIsDirectoryError]
            - [`UserAccountsFileIsNotJSONError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileIsNotJSONError]
            - [`UserAccountsFileSchemaError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileSchemaError]
            - [`UserAccountsFileContainsDuplicateUsernamesError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileContainsDuplicateUsernamesError]
        - [`UserAccountAuthenticationError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountAuthenticationError]
        - [`UserAccountManagementError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountManagementError]
            - [`UserAccountUsernameAlreadyExistsError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountUsernameAlreadyExistsError]
            - [`EmptyUserAccountUsernameError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.EmptyUserAccountUsernameError]
            - [`EmptyUserAccountPasswordError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.EmptyUserAccountPasswordError]
            - [`InvalidUserAccountRoleError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.InvalidUserAccountRoleError]
"""

from pathlib import Path

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class UserAccountsServiceError(BaseServiceError):
    """Base exception for all errors that occur within the user accounts service."""

    code = "USER_ACCOUNTS_SERVICE_ERROR"


class UserAccountNotFoundError(UserAccountsServiceError):
    """Base exception raised when the requested user account was not found in the user
    accounts service.
    """

    code = "USER_ACCOUNT_NOT_FOUND_ERROR"


class UserAccountIDNotFoundError(UserAccountNotFoundError):
    """Raised when the requested user account was not found by user account ID in the
    user accounts service.
    """

    code = "USER_ACCOUNT_ID_NOT_FOUND_ERROR"

    def __init__(
        self,
        user_account_id: str,
    ):
        super().__init__(
            message=(
                "Failed to find the requested user account. No user account could "
                f"be found with the provided user account ID '{user_account_id}'."
            ),
            detail={
                "user_account_id": user_account_id,
            },
        )


class UserAccountUsernameNotFoundError(UserAccountNotFoundError):
    """Raised when the requested user account was not found by username in the user
    accounts service.
    """

    code = "USER_ACCOUNT_USERNAME_NOT_FOUND_ERROR"

    def __init__(
        self,
        username: str,
    ):
        super().__init__(
            message=(
                "Failed to find the requested user account. No user account could "
                f"be found with the provided username '{username}'."
            ),
        )


class UserAccountsFileError(UserAccountsServiceError):
    """Base exception for all errors that occur when accessing or processing the user
    accounts file.
    """

    code = "USER_ACCOUNTS_FILE_ERROR"


class UserAccountsFileNotFoundError(UserAccountsFileError):
    """Raised when the user accounts file does not exist at the specified filepath."""

    code = "USER_ACCOUNTS_FILE_NOT_FOUND_ERROR"

    def __init__(
        self,
        user_accounts_filepath: str,
    ):
        super().__init__(
            message=(
                "Failed to access the user accounts file "
                f"'{user_accounts_filepath}'. The filepath does not appear to exist."
            ),
        )


class UserAccountsFileAccessError(UserAccountsFileError):
    """Base exception for all errors that occur when the process lacks the required
    permissions to access the user accounts file.
    """

    code = "USER_ACCOUNTS_FILE_ACCESS_ERROR"


class UserAccountsFileReadAccessError(UserAccountsFileAccessError):
    """Raised when the process does not have read permissions for the user accounts file."""

    code = "USER_ACCOUNTS_FILE_READ_ACCESS_ERROR"

    def __init__(
        self,
        user_accounts_filepath: str,
    ):
        super().__init__(
            message=(
                "Failed to read the provided user accounts file "
                f"'{user_accounts_filepath}'. The process does not have the required "
                "permissions to read the file."
            ),
        )


class UserAccountsFileWriteAccessError(UserAccountsFileAccessError):
    """Raised when the process does not have write permissions for the user accounts file."""

    code = "USER_ACCOUNTS_FILE_WRITE_ACCESS_ERROR"

    def __init__(
        self,
        user_accounts_filepath: str,
    ):
        super().__init__(
            message=(
                "Failed to write to the user accounts file "
                f"'{user_accounts_filepath}'. The process does not have the required "
                "permissions to write to the file."
            ),
        )


class UserAccountsFilepathIsDirectoryError(UserAccountsFileError):
    """Raised when the user accounts filepath points to a directory instead of a file."""

    code = "USER_ACCOUNTS_FILEPATH_IS_DIRECTORY_ERROR"

    def __init__(
        self,
        user_accounts_filepath: str,
    ):
        super().__init__(
            message=(
                "Failed to access the user accounts file "
                f"'{user_accounts_filepath}'. The provided filepath points to an "
                "existing directory where a file was expected."
            ),
        )


class UserAccountsFileIsNotJSONError(UserAccountsFileError):
    """Raised when the user accounts file does not contain valid JSON data."""

    code = "USER_ACCOUNTS_FILE_IS_NOT_JSON_ERROR"

    def __init__(
        self,
        user_accounts_filepath: str,
    ):
        super().__init__(
            message=(
                "Failed to process the user accounts file "
                f"'{user_accounts_filepath}'. The provided file does not contain "
                "valid JSON data."
            ),
        )


class UserAccountsFileSchemaError(UserAccountsFileError):
    """Raised when the user accounts file fails JSON schema validation."""

    code = "USER_ACCOUNTS_FILE_SCHEMA_ERROR"

    def __init__(
        self,
        user_accounts_filepath: str,
        json_schema_error_message,
    ):
        super().__init__(
            message=(
                f"Failed to process the user accounts file "
                f"'{user_accounts_filepath}'. The provided file failed JSON schema "
                f"validation: {json_schema_error_message}."
            ),
        )


class UserAccountsFileContainsDuplicateUsernamesError(
    UserAccountsFileError,
):
    """Raised when the user accounts file contains multiple user account entries with
    the same username.
    """

    code = "USER_ACCOUNTS_FILE_CONTAINS_DUPLICATE_USERNAMES_ERROR"

    def __init__(
        self,
        user_accounts_filepath: str | Path,
        duplicate_username: str,
    ):
        super().__init__(
            message=(
                "Failed to process the user accounts file "
                f"'{user_accounts_filepath}'. The user accounts file contains user "
                f"account entries with the duplicate username '{duplicate_username}'."
            ),
        )


class UserAccountAuthenticationError(UserAccountsServiceError):
    """Raised when a user account fails to authenticate due to invalid credentials."""

    code = "USER_ACCOUNT_AUTHENTICATION_ERROR"

    def __init__(self):
        super().__init__(
            message=(
                "Failed to authenticate the user account. Invalid credentials were "
                "provided."
            ),
        )


class UserAccountManagementError(UserAccountsServiceError):
    """Base exception for all errors that occur during user account creation or
    modification operations.
    """

    code = "USER_ACCOUNT_MANAGEMENT_ERROR"


class UserAccountUsernameAlreadyExistsError(UserAccountManagementError):
    """Raised when attempting to create or modify a user account with a username that is
    already in use by another user account.
    """

    code = "USER_ACCOUNT_USERNAME_ALREADY_EXISTS_ERROR"

    @classmethod
    def _during_user_account_creation(
        cls,
        username: str,
    ) -> UserAccountUsernameAlreadyExistsError:
        return cls(
            message=(
                f"Failed to create the user account. The username '{username}' is "
                f"already in use by another user account."
            ),
        )

    @classmethod
    def _during_user_account_modification(
        cls,
        user_account_str: str,
        username: str,
    ) -> UserAccountUsernameAlreadyExistsError:
        return cls(
            message=(
                f"Failed to modify the user account '{user_account_str}'. The new "
                f"username '{username}' is already in use by another user account."
            ),
        )

    @classmethod
    def _during_user_accounts_file_loading(
        cls,
        user_accounts_filepath: str,
        username: str,
    ) -> UserAccountUsernameAlreadyExistsError:
        return cls(
            message=(
                f"Failed to load the user account from the user accounts file "
                f"'{user_accounts_filepath}'. The username '{username}' is already in "
                f"use by another user account."
            ),
            detail={
                "user_accounts_filepath": str(user_accounts_filepath),
                "username": str(username),
            },
        )


class EmptyUserAccountUsernameError(UserAccountManagementError):
    """Raised when attempting to create or modify a user account with an empty username."""

    code = "EMPTY_USER_ACCOUNT_USERNAME_ERROR"

    @classmethod
    def _during_user_account_creation(cls) -> EmptyUserAccountUsernameError:
        return cls(
            message=(
                "Failed to create the user account. The provided username "
                "cannot be empty."
            ),
        )

    @classmethod
    def _during_user_account_modification(
        cls,
        user_account_str: str,
    ) -> EmptyUserAccountUsernameError:
        return cls(
            message=(
                f"Failed to modify the user account {user_account_str}. The provided "
                f"username cannot be empty."
            ),
        )


class EmptyUserAccountPasswordError(UserAccountManagementError):
    """Raised when attempting to create or modify a user account with an empty password."""

    code = "EMPTY_USER_ACCOUNT_PASSWORD_ERROR"

    @classmethod
    def _during_user_account_creation(cls) -> EmptyUserAccountPasswordError:
        return cls(
            message=(
                "Failed to create the user account. The provided password "
                "cannot be empty."
            ),
        )

    @classmethod
    def _during_user_account_modification(
        cls,
        user_account_str: str,
    ) -> EmptyUserAccountPasswordError:
        return cls(
            message=(
                f"Failed to modify the user account {user_account_str}. The provided "
                "password cannot be empty."
            ),
        )


class InvalidUserAccountRoleError(UserAccountManagementError):
    """Raised when attempting to create or modify a user account with an invalid role.
    Valid roles are 'ADMIN', 'OPERATOR', or 'SPECTATOR'.
    """

    code = "INVALID_USER_ACCOUNT_ROLE_ERROR"

    @classmethod
    def _during_user_account_creation(cls, role: str) -> InvalidUserAccountRoleError:
        return cls(
            message=(
                f"Failed to create the user account. The provided role '{role}' "
                "is not a valid role. Check that the provided role is one of 'ADMIN', "
                "'OPERATOR', or 'SPECTATOR'."
            ),
        )

    @classmethod
    def _during_user_account_modification(
        cls,
        user_account_str: str,
        role: str,
    ) -> InvalidUserAccountRoleError:
        return cls(
            message=(
                f"Failed to modify the user account '{user_account_str}'. The provided "
                f"role '{role}' is not a valid role. Check that the provided role is "
                f"one of 'ADMIN', 'OPERATOR', or 'SPECTATOR'."
            ),
        )
