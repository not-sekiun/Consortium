"""
Exception hierarchy for the user accounts service.
- BaseServiceException: Base class for all service-related exceptions.
 - UserAccountsServiceError: Base for all user accounts service exceptions.
   - UserAccountNotFoundError: User account not found.
     - UserAccountIDNotFoundError: User account with provided ID not found.
     - UserAccountUsernameNotFoundError: User account with provided username not found.
   - UserAccountsFileError: Error processing user accounts file.
     - UserAccountsFileNotFoundError: User accounts file not found.
     - UserAccountsFileAccessError: Insufficient access permissions for user accounts
     file.
       - UserAccountsFileWriteAccessError: Insufficient write permissions for file.
       - UserAccountsFileReadAccessError: Insufficient read permissions for file.
     - UserAccountsFilepathIsDirectoryError: User accounts filepath points to a
     directory.
     - UserAccountsFileIsNotJSONError: User accounts file not valid JSON.
     - UserAccountsFileSchemaError: User accounts file does not conform to expected
     schema.
       - UserAccountsFileContainsDuplicateUsernamesError: File contains duplicate
       usernames.
   - UserAccountAuthenticationError: Invalid credentials provided for authentication.
   - UserAccountManagementError: Error creating or modifying user account.
     - UserAccountUsernameAlreadyExistsError: Provided username already exists.
     - EmptyUserAccountUsernameError: Provided username cannot be empty.
     - EmptyUserAccountPasswordError: Provided password cannot be empty.
     - InvalidUserAccountRoleError: Provided role is not valid.
     - IdenticalUserAccountUsernameError: New username identical to previous.
     - IdenticalUserAccountPasswordError: New password identical to previous.
     - IdenticalUserAccountRoleError: New role identical to previous.
"""

from pathlib import Path

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)
from consortium.server.objects.user_account_objects import UserRole


class UserAccountsServiceError(BaseServiceException):
    def __init__(
        self,
        message: str = ("An error occurred in the user accounts service."),
    ):
        super().__init__(message=message)


class UserAccountNotFoundError(UserAccountsServiceError):
    def __init__(
        self,
        message: str = ("Failed to find the requested user account."),
    ):
        super().__init__(message=message)


class UserAccountIDNotFoundError(UserAccountNotFoundError):
    def __init__(
        self,
        user_account_id: str,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "Failed to find the requested user account. No user account could "
                f"be found with the provided user account ID '{user_account_id}'."
            )
        super().__init__(message=message)


class UserAccountUsernameNotFoundError(UserAccountNotFoundError):
    def __init__(
        self,
        username: str,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "Failed to find the requested user account. No user account could "
                f"be found with the provided username '{username}'."
            )
        super().__init__(message=message)


class UserAccountsFileError(UserAccountsServiceError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "An error occurred while attempting to process the provided user "
                f"accounts file '{user_accounts_filepath}'."
            )
        super().__init__(message=message)


class UserAccountsFileNotFoundError(UserAccountsFileError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "Failed to access the provided user accounts file "
                f"'{user_accounts_filepath}'. The filepath does not appear to exist."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFileAccessError(UserAccountsFileError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "Failed to access the provided user accounts file "
                f"'{user_accounts_filepath}'. The process has insufficient access "
                "permissions."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFileReadAccessError(UserAccountsFileAccessError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "Failed to read the provided user accounts file "
                f"'{user_accounts_filepath}'. The process has insufficient read "
                "permissions."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFileWriteAccessError(UserAccountsFileAccessError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "Failed to write to the provided user accounts file "
                f"'{user_accounts_filepath}'. The process has insufficient write "
                "permissions."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFilepathIsDirectoryError(UserAccountsFileError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "Failed to access the provided user accounts file "
                f"'{user_accounts_filepath}'. The provided filepath points to an "
                "existing directory when a file was expected."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFileIsNotJSONError(UserAccountsFileError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "Failed to decode the provided user accounts file "
                f"'{user_accounts_filepath}'. The provided file does not contain "
                "valid JSON data."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFileSchemaError(UserAccountsFileError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "Failed to decode the provided user accounts file "
                f"'{user_accounts_filepath}'. The provided file does not contain "
                "JSON data that conforms to the expected JSON schema."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFileContainsDuplicateUsernamesError(
    UserAccountsFileSchemaError,
):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        duplicate_username: str,
        message: str | None = None,
    ):
        if message is None:
            message = (
                "Failed to decode the provided user accounts file "
                f"'{user_accounts_filepath}'. The user accounts file contains entries "
                f"with a duplicate username '{duplicate_username}'."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountAuthenticationError(UserAccountsServiceError):
    def __init__(
        self,
        message: str = (
            "Unable to authenticate user account. Invalid credentials were provided."
        ),
    ):
        super().__init__(message=message)


class UserAccountManagementError(UserAccountsServiceError):
    def __init__(
        self,
        message: str = "An error occurred while creating or modifying a user account.",
    ):
        super().__init__(message=message)


class UserAccountUsernameAlreadyExistsError(UserAccountManagementError):
    def __init__(
        self,
        username: str,
        message: str | None = None,
    ):
        if message is None:
            message = (
                f"Unable to create or modify a user account. The username '{username}' "
                "is already in use and user accounts cannot have duplicate usernames."
            )
        super().__init__(message=message)


class EmptyUserAccountUsernameError(UserAccountManagementError):
    def __init__(self, message: str | None = None):
        if message is None:
            message = (
                "Unable to create or modify a user account. The provided username "
                "cannot be empty."
            )
        super().__init__(message=message)


class EmptyUserAccountPasswordError(UserAccountManagementError):
    def __init__(self, message: str | None = None):
        if message is None:
            message = (
                "Unable to create or modify a user account. The provided password "
                "cannot be empty."
            )
        super().__init__(message=message)


class InvalidUserAccountRoleError(UserAccountManagementError):
    def __init__(self, role: str, message: str | None = None):
        if message is None:
            message = (
                "Unable to create or modify a user account. The provided role "
                f"'{role}' is not a valid role. Valid roles are 'ADMIN', 'OPERATOR', "
                f"and 'SPECTATOR'."
            )
        self.role = role
        super().__init__(message=message)


class IdenticalUserAccountUsernameError(UserAccountManagementError):
    def __init__(self, username: str, message: str | None = None):
        if message is None:
            message = (
                "Unable to modify the user account's usernames. The new username "
                f"'{username}' is identical to the previous username. "
                "Provide a different username."
            )
        super().__init__(message=message)


class IdenticalUserAccountPasswordError(UserAccountManagementError):
    def __init__(self, message: str | None = None):
        if message is None:
            message = (
                "Unable to modify the user account's password. The new password "
                "is identical to the previous password. Provide a different password."
            )
        super().__init__(message=message)


class IdenticalUserAccountRoleError(UserAccountManagementError):
    def __init__(self, role: str | UserRole, message: str | None = None):
        if message is None:
            message = (
                f"Unable to modify the user account's role. The new role '{role}' is "
                "identical to the previous role. Provide a different role."
            )
        super().__init__(message=message)
