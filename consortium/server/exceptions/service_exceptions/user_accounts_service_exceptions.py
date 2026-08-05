"""
Exception hierarchy:

- [`BaseServiceError`][consortium.server.exceptions.service_exceptions.base_service_exception.BaseServiceError]
    - [`UserAccountsServiceError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsServiceError]
        - [`UserAccountNotFoundError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountNotFoundError]
            - [`UserAccountIDNotFoundError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountIDNotFoundError]
            - [`UserAccountUsernameNotFoundError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountUsernameNotFoundError]
        - [`UserAccountsFileError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileError]
            - [`UserAccountsFileSystemError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileSystemError]
            - [`UserAccountsFileContentError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileContentError]
                - [`UserAccountsFileEncodingError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileEncodingError]
                - [`UserAccountsFileJSONError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileJSONError]
                - [`UserAccountsFileSchemaError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileSchemaError]
                - [`UserAccountsFileDuplicateUsernamesError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountsFileDuplicateUsernamesError]
        - [`UserAccountAuthenticationError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountAuthenticationError]
        - [`UserAccountManagementError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountManagementError]
            - [`UserAccountUsernameAlreadyExistsError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.UserAccountUsernameAlreadyExistsError]
            - [`EmptyUserAccountUsernameError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.EmptyUserAccountUsernameError]
            - [`EmptyUserAccountPasswordError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.EmptyUserAccountPasswordError]
            - [`InvalidUserAccountRoleError`][consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions.InvalidUserAccountRoleError]
"""

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceError,
)


class UserAccountsServiceError(BaseServiceError):
    """Base exception for all errors that occur within the user accounts service.

    Attributes:
        code: A stable machine-readable string identifying the specific error.
        message: A human-readable description of what went wrong and, where possible,
            how to resolve it.
        detail: Optional structured context about the error, or None when there is
            none.
    """

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
            detail={
                "username": username,
            },
        )


class UserAccountsFileError(UserAccountsServiceError):
    """Base exception for every failure to get the user accounts file's data on or off
    disk.

    Catch this to handle "the user accounts did not make it in or out" without caring
    why. To distinguish a filesystem fault from a bad file, catch
    `UserAccountsFileSystemError` or `UserAccountsFileContentError` instead.
    """

    code = "USER_ACCOUNTS_FILE_ERROR"


class UserAccountsFileSystemError(UserAccountsFileError):
    """Raised when the user accounts file cannot be read from or written to disk.

    This covers every way the filesystem can refuse the operation: the file does not
    exist, the process lacks the required permissions, the configured path points at a
    directory, the disk is full. They share one type because no caller can act differently
    on any of them. All of them mean the operation did not happen, and the specific cause
    is carried in `message` and `detail` for whoever has to fix it.

    These are server side faults or misconfiguration: no user accounts operation takes a
    filesystem path from a client, so a failure here reflects the state of the machine the
    server is running on, the path it was configured with, or a bug in the code that
    supplied that path.

    A file the filesystem hands over successfully but whose contents are wrong is reported
    separately, through `UserAccountsFileContentError`.
    """

    code = "USER_ACCOUNTS_FILE_SYSTEM_ERROR"

    def __init__(self, operation: str, path: str, underlying_error: str):
        super().__init__(
            message=f"Failed to {operation} at the path '{path}'. {underlying_error}",
            detail={
                "operation": operation,
                "path": path,
                "underlying_error": underlying_error,
            },
        )

    @classmethod
    def _path_is_a_directory(
        cls,
        operation: str,
        path: str,
    ) -> UserAccountsFileSystemError:
        # Checked up front by the service rather than left to `open()`, because the
        # `OSError` that results does not identify the problem on every platform: Windows
        # reports opening a directory as `PermissionError: [Errno 13] Permission denied`,
        # which sends whoever has to fix it looking at file permissions rather than at the
        # configured path. A missing file needs no such help, since `FileNotFoundError`
        # already says exactly what is wrong.
        return cls(
            operation=operation,
            path=path,
            underlying_error=(
                "The path points to an existing directory where a file was expected."
            ),
        )


class UserAccountsFileContentError(UserAccountsFileError):
    """Base exception for all errors that occur when the user accounts file's contents
    are wrong.

    The filesystem handed the file's bytes over successfully, so this is fixed by
    correcting the file rather than by changing the state of the machine or the
    configured path.
    """

    code = "USER_ACCOUNTS_FILE_CONTENT_ERROR"


class UserAccountsFileEncodingError(UserAccountsFileContentError):
    """Raised when the user accounts file's bytes cannot be decoded as UTF-8.

    Pinning the encoding on the read removes the case where the file was written as UTF-8
    elsewhere and read back under a different platform default, but not this one, where
    the bytes are not valid UTF-8 under any reading.

    There is no encoding counterpart on the write path. The accounts are serialized with
    `json.dumps`, whose default `ensure_ascii=True` escapes every non-ASCII character, so
    the text handed to the encoder is always pure ASCII and cannot fail to encode.
    """

    code = "USER_ACCOUNTS_FILE_ENCODING_ERROR"

    def __init__(
        self,
        path: str,
        underlying_error: str,
    ):
        super().__init__(
            message=(
                f"Failed to read the user accounts file '{path}'. The file's contents "
                f"are not valid UTF-8 text. {underlying_error}"
            ),
            detail={
                "path": path,
                "underlying_error": underlying_error,
            },
        )


class UserAccountsFileJSONError(UserAccountsFileContentError):
    """Raised when the user accounts file does not contain valid JSON data."""

    code = "USER_ACCOUNTS_FILE_JSON_ERROR"

    def __init__(
        self,
        path: str,
    ):
        super().__init__(
            message=(
                f"Failed to process the user accounts file '{path}'. The provided file "
                "does not contain valid JSON data."
            ),
            detail={"path": path},
        )


class UserAccountsFileSchemaError(UserAccountsFileContentError):
    """Raised when the user accounts file does not conform to the expected schema.

    Covers the shape of the file as a whole and of every account entry in it: a top level
    value that is not an array, an entry missing a required field, an empty username or
    password, and an entry carrying a field the schema does not define.
    """

    code = "USER_ACCOUNTS_FILE_SCHEMA_ERROR"

    def __init__(
        self,
        path: str,
        validation_error_message: str,
    ):
        super().__init__(
            message=(
                f"Failed to process the user accounts file '{path}'. The provided file "
                f"failed validation. {validation_error_message}"
            ),
            detail={
                "path": path,
                "validation_error_message": validation_error_message,
            },
        )


class UserAccountsFileDuplicateUsernamesError(UserAccountsFileContentError):
    """Raised when the user accounts file contains multiple user account entries with
    the same username.
    """

    code = "USER_ACCOUNTS_FILE_DUPLICATE_USERNAMES_ERROR"

    def __init__(
        self,
        path: str,
        duplicate_username: str,
    ):
        super().__init__(
            message=(
                f"Failed to process the user accounts file '{path}'. The user accounts "
                f"file contains user account entries with the duplicate username "
                f"'{duplicate_username}'."
            ),
            detail={
                "path": path,
                "duplicate_username": duplicate_username,
            },
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
        path: str,
        username: str,
    ) -> UserAccountUsernameAlreadyExistsError:
        return cls(
            message=(
                f"Failed to load the user account from the user accounts file "
                f"'{path}'. The username '{username}' is already in "
                f"use by another user account."
            ),
            detail={
                "path": str(path),
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

    @classmethod
    def _during_user_accounts_file_loading(
        cls,
        path: str,
        username: str,
        role: str,
    ) -> InvalidUserAccountRoleError:
        return cls(
            message=(
                f"Failed to load the user account '{username}' from the user accounts "
                f"file '{path}'. The role '{role}' is not a valid "
                f"role. Check that the role is one defined in the role permissions file."
            ),
            detail={
                "path": str(path),
                "username": str(username),
                "role": str(role),
            },
        )
