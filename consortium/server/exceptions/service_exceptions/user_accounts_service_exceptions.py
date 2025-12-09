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
from typing import Literal

from consortium.server.exceptions.service_exceptions.base_service_exception import (
    BaseServiceException,
)
from consortium.server.objects.user_account_objects import UserRole


class UserAccountsServiceError(BaseServiceException):
    code = "USER_ACCOUNTS_SERVICE_ERROR"


class UserAccountNotFoundError(UserAccountsServiceError):
    code = "USER_ACCOUNT_NOT_FOUND_ERROR"


class UserAccountIDNotFoundError(UserAccountNotFoundError):
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
        )


class UserAccountUsernameNotFoundError(UserAccountNotFoundError):
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
    code = "USER_ACCOUNTS_FILE_ERROR"


class UserAccountsFileNotFoundError(UserAccountsFileError):
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
    code = "USER_ACCOUNTS_FILE_ACCESS_ERROR"


class UserAccountsFileReadAccessError(UserAccountsFileAccessError):
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
    code = "USER_ACCOUNT_AUTHENTICATION_ERROR"

    def __init__(
        self,
    ):
        super().__init__(
            message=(
                "Failed to authenticate user account. Invalid credentials were "
                "provided."
            ),
        )


class UserAccountManagementError(UserAccountsServiceError):
    code = "USER_ACCOUNT_MANAGEMENT_ERROR"


class UserAccountUsernameAlreadyExistsError(UserAccountManagementError):
    code = "USER_ACCOUNT_USERNAME_ALREADY_EXISTS_ERROR"

    @classmethod
    def during_user_account_creation(
        cls,
        username: str,
    ) -> "UserAccountUsernameAlreadyExistsError":
        return cls(
            message=(
                f"Failed to create the user account. The username '{username}' is "
                f"already in use by another user account."
            ),
        )

    @classmethod
    def during_user_account_modification(
        cls,
        username: str,
        user_account: str,
    ) -> "UserAccountUsernameAlreadyExistsError":
        return cls(
            message=(
                f"Failed to modify the user account '{user_account}'. The new "
                f"username '{username}' is already in use by another user account."
            ),
        )

    @classmethod
    def during_user_accounts_file_loading(
        cls,
        username: str,
        user_accounts_filepath: str,
    ) -> "UserAccountUsernameAlreadyExistsError":
        return cls(
            message=(
                f"Failed to load the user account from the user accounts file "
                f"'{user_accounts_filepath}'. The username '{username}' is already in "
                f"use by another user account."
            ),
        )


class EmptyUserAccountUsernameError(UserAccountManagementError):
    code = "EMPTY_USER_ACCOUNT_USERNAME_ERROR"

    @classmethod
    def during_user_account_creation(cls) -> "EmptyUserAccountUsernameError":
        return cls(
            message=(
                "Failed to create the user account. The provided username "
                "cannot be empty."
            ),
        )

    @classmethod
    def during_user_account_modification(
        cls,
        user_account: str,
    ) -> "EmptyUserAccountUsernameError":
        return cls(
            message=(
                f"Failed to modify the user account {user_account}. The provided "
                f"username cannot be empty."
            ),
        )


class EmptyUserAccountPasswordError(UserAccountManagementError):
    code = "EMPTY_USER_ACCOUNT_PASSWORD_ERROR"

    @classmethod
    def during_user_account_creation(cls) -> "EmptyUserAccountPasswordError":
        return cls(
            message=(
                "Failed to create the user account. The provided password "
                "cannot be empty."
            ),
        )

    @classmethod
    def during_user_account_modification(
        cls,
        user_account: str,
    ) -> "EmptyUserAccountPasswordError":
        return cls(
            message=(
                f"Failed to modify the user account {user_account}. The provided "
                "password cannot be empty."
            ),
        )


class InvalidUserAccountRoleError(UserAccountManagementError):
    code = "INVALID_USER_ACCOUNT_ROLE_ERROR"

    @classmethod
    def during_user_account_creation(cls, role: str) -> "InvalidUserAccountRoleError":
        return cls(
            message=(
                f"Failed to create the user account. The provided role '{role}' "
                "is not a valid role which must be one of 'ADMIN', 'OPERATOR', or "
                "'SPECTATOR'."
            ),
        )

    @classmethod
    def during_user_account_modification(
        cls,
        role: str,
        user_account: str,
    ) -> "InvalidUserAccountRoleError":
        return cls(
            message=(
                f"Failed to modify the user account '{user_account}'. The provided "
                f"role '{role}' is not a valid role which must be one of 'ADMIN', "
                f"'OPERATOR', or 'SPECTATOR'."
            ),
        )


class IdenticalUserAccountUsernameError(UserAccountManagementError):
    code = "IDENTICAL_USER_ACCOUNT_USERNAME_ERROR"

    def __init__(self, user_account_str: str, username: str):
        super().__init__(
            message=(
                f"Failed to modify user account '{user_account_str}'. The newly "
                f"provided username '{username}' is identical to the previously used "
                f"username."
            ),
        )


class IdenticalUserAccountPasswordError(UserAccountManagementError):
    code = "IDENTICAL_USER_ACCOUNT_PASSWORD_ERROR"

    def __init__(self, user_account_str: str):
        super().__init__(
            message=(
                f"Failed to modify user account '{user_account_str}'. The newly "
                f"provided password is identical to the previously used password."
            ),
        )


class IdenticalUserAccountRoleError(UserAccountManagementError):
    code = "IDENTICAL_USER_ACCOUNT_ROLE_ERROR"

    def __init__(self, user_account_str: str, role: str | UserRole):
        super().__init__(
            message=(
                f"Failed to modify user account '{user_account_str}'. The newly "
                f"provided role '{role}' is identical to the previously assigned role."
            ),
        )
