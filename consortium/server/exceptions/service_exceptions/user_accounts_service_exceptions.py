"""
Exception hierarchy for the user accounts service.

- BaseServiceException: Base class for all service-related exceptions
  - UserAccountsServiceError: Base class for all exceptions related to the user accounts service
    - UserAccountNotFoundServiceError: Raised when a requested user accounts is not found
      - InvalidUserAccountIDServiceError: Raised when the provided user account ID is not found.
      - InvalidUserAccountUsernameServiceError: Raised when the provided username is not found.
    - UserAccountsFileServiceError: Raised when an error occurs while processing a user accounts file.
      - UserAccountsFileNotFoundServiceError: Raised when the user accounts file cannot be found.
      - UserAccountsFileAccessServiceError: Raised when an error arises with accessing a user accounts file.
        - UserAccountsFileWriteAccessServiceError: Raised when an error arised with writing to the user accounts file.
        - UserAccountsFileReadAccessServiceError: Raised when an error arised with writing to the user accounts file.
      - UserAccountsFilepathIsDirectoryServiceError: Raised when the user accounts filepath does not point to a file.
      - UserAccountsFileIsNotJSONServiceError: Raised when the user accounts file is not a valid JSON file.
      - UserAccountsFileSchemaServiceError: Raised when the user accounts file fails to conform to the expected schema.
        - UserAccountsFileContainsDuplicateUsernamesServiceError: Raised when the user accounts file has multiple usernames.
    - UserAccountAuthenticationServiceError: Raised when an error occurs during user account authentication.
    - UserAccountManagementServiceError: Raised when an error occurs while modifying/creating a user account.
      - UserAccountUsernameAlreadyExistsServiceError: Raised when a user account is created in the service with a username that already exists.
      - EmptyUserAccountUsernameServiceError: Raised when a user account is created with an empty username.
      - EmptyUserAccountPasswordServiceError: Raised when a user account is created with an empty password.
      - InvalidUserAccountRoleServiceError: Raised when a user account is created with a roles that does not exist.
      - IdenticalUserAccountUsernameServiceError: Raised when a user account is created with a username that is identical to the previous username.
      - IdenticalUserAccountPasswordServiceError: Raised when a user account is created with a password that is identical to the previous password.
      - IdenticalUserAccountRoleServiceError: Raised when a user account is created with a role that is identical to the previous role.
"""

from pathlib import Path

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)
from consortium.server.objects.user_account_objects import UserRole


class UserAccountsServiceError(BaseServiceException):
    def __init__(
        self,
        message: str = (
            "An unexpected error occurred within the user accounts service."
        ),
    ):
        super().__init__(message=message)


class UserAccountNotFoundServiceError(UserAccountsServiceError):
    def __init__(
        self,
        message: str = (
            "The requested user account was not found within the user accounts service."
        ),
    ):
        super().__init__(message=message)


class InvalidUserAccountIDServiceError(UserAccountNotFoundServiceError):
    def __init__(
        self,
        user_account_id: str,
        message: str | None = None,
    ):
        if message is None:
            message = (
                f"No user account found with the provided user account ID "
                f"'{user_account_id}'."
            )
        super().__init__(message=message)


class InvalidUserAccountUsernameServiceError(UserAccountNotFoundServiceError):
    def __init__(
        self,
        username: str,
        message: str | None = None,
    ):
        if message is None:
            message = (
                f"No user account found with the provided user account username "
                f"'{username}'."
            )
        super().__init__(message=message)


class UserAccountsFileServiceError(UserAccountsServiceError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                f"An unexpected error occurred while attempting to process the user "
                f"accounts file '{user_accounts_filepath}'."
            )
        super().__init__(message=message)


class UserAccountsFileNotFoundServiceError(UserAccountsFileServiceError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                f"User accounts file was not found at the provided filepath "
                f"'{user_accounts_filepath}'."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFileAccessServiceError(UserAccountsFileServiceError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                f"Unable to access the user accounts file '{user_accounts_filepath}' "
                f"due to insufficient access permissions."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFileReadAccessServiceError(UserAccountsFileAccessServiceError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                f"Unable to read the user accounts file '{user_accounts_filepath}' "
                f"due to insufficient read access permissions."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFileWriteAccessServiceError(UserAccountsFileAccessServiceError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                f"Unable to write to the user accounts file '{user_accounts_filepath}' "
                f"due to insufficient write access permissions."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFilepathIsDirectoryServiceError(UserAccountsFileServiceError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                f"User accounts filepath '{user_accounts_filepath}' points to a "
                f"directory when a file was expected."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFileIsNotJSONServiceError(UserAccountsFileServiceError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                f"User accounts filepath '{user_accounts_filepath}' does not contain "
                "valid decodable JSON data."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFileSchemaServiceError(UserAccountsFileServiceError):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        message: str | None = None,
    ):
        if message is None:
            message = (
                f"User accounts file '{user_accounts_filepath}' does not contain "
                f"JSON data that conforms to the expected JSON schema."
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountsFileContainsDuplicateUsernamesServiceError(
    UserAccountsFileSchemaServiceError,
):
    def __init__(
        self,
        user_accounts_filepath: str | Path,
        duplicate_username: str,
        message: str | None = None,
    ):
        if message is None:
            message = (
                f"User accounts file '{user_accounts_filepath}' contains user account "
                f"entries with duplicate usernames: {duplicate_username}"
            )
        super().__init__(user_accounts_filepath=user_accounts_filepath, message=message)


class UserAccountAuthenticationServiceError(UserAccountsServiceError):
    def __init__(
        self,
        message: str = (
            "Invalid credentials were provided when attempting to authenticate the "
            "user account."
        ),
    ):
        super().__init__(message=message)


class UserAccountManagementServiceError(UserAccountsServiceError):
    def __init__(
        self,
        message: str = (
            "An unexpected error occurred while attempting to modify or create the "
            "user account."
        ),
    ):
        super().__init__(message=message)


class UserAccountUsernameAlreadyExistsServiceError(UserAccountManagementServiceError):
    def __init__(
        self,
        existing_username: str,
        message: str | None = None,
    ):
        if message is None:
            message = (
                f"A user account with the username '{existing_username}' already "
                "exists within the user accounts service."
            )
        super().__init__(message=message)


class EmptyUserAccountUsernameServiceError(UserAccountManagementServiceError):
    def __init__(self, message: str | None = None):
        if message is None:
            message = "The provided username cannot be empty."
        super().__init__(message=message)


class EmptyUserAccountPasswordServiceError(UserAccountManagementServiceError):
    def __init__(self, message: str | None = None):
        if message is None:
            message = "The provided password cannot be empty."
        super().__init__(message=message)


class InvalidUserAccountRoleServiceError(UserAccountManagementServiceError):
    def __init__(self, role: str, message: str | None = None):
        if message is None:
            message = f"The provided role '{role}' is not a valid role."
        self.role = role
        super().__init__(message=message)


class IdenticalUserAccountUsernameServiceError(UserAccountManagementServiceError):
    def __init__(self, username: str, message: str | None = None):
        if message is None:
            message = (
                f"The provided username '{username}' is identical to the previous "
                "username. Please provide a different username."
            )
        super().__init__(message=message)


class IdenticalUserAccountPasswordServiceError(UserAccountManagementServiceError):
    def __init__(self, message: str | None = None):
        if message is None:
            message = (
                "The provided password is identical to the previous password. "
                "Please provide a different password."
            )
        super().__init__(message=message)


class IdenticalUserAccountRoleServiceError(UserAccountManagementServiceError):
    def __init__(self, role: str | UserRole, message: str | None = None):
        if message is None:
            message = (
                f"The provided role '{role}' is identical to the previous role. "
                "Please provide a different role."
            )
        super().__init__(message=message)
