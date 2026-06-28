import json
import pathlib
import uuid
from pathlib import Path

import jsonschema
from loguru import logger

from consortium.server.exceptions.consortium_exceptions.user_accounts_consortium_exceptions import (
    EmptyUserAccountPasswordError,
    EmptyUserAccountUsernameError,
    InvalidUserAccountRoleError,
    UserAccountAuthenticationError,
    UserAccountIDNotFoundError,
    UserAccountsFileContainsDuplicateUsernamesError,
    UserAccountsFileIsNotJSONError,
    UserAccountsFileNotFoundError,
    UserAccountsFilepathIsDirectoryError,
    UserAccountsFileReadAccessError,
    UserAccountsFileSchemaError,
    UserAccountsFileWriteAccessError,
    UserAccountsServiceError,
    UserAccountUsernameAlreadyExistsError,
    UserAccountUsernameNotFoundError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.models.user_account_models import UserAccountModel
from consortium.server.services.authorization_service import AuthorizationService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)


class UserAccountsService:
    def __init__(
        self,
        user_accounts_json_file: pathlib.Path,
        authorization_service: AuthorizationService,
    ) -> None:
        self._user_accounts_json_file = user_accounts_json_file
        self._authorization_service = authorization_service
        self._user_accounts = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "User Accounts Service"

    def __repr__(self) -> str:
        return "UserAccountsService()"

    @log_and_propagate_error_on_service_method
    def get_user_account_by_user_account_id(
        self,
        user_account_id: str | uuid.UUID,
    ) -> UserAccountModel:
        """Returns a user account by its ID.

        Args:
            user_account_id (str | uuid.UUID): The ID of the user account to retrieve.

        Returns:
            UserAccountModel: The requested user account.

        Raises:
            UserAccountIDNotFoundError: If no user account with the given ID exists.
        """
        user_account_id = normalize_uuid(user_account_id)

        try:
            user_account = self._user_accounts[user_account_id]
        except KeyError:
            raise UserAccountIDNotFoundError(
                user_account_id=user_account_id,
            ) from None

        self._logger.debug("Retrieved user account: {!r}", user_account)
        return user_account

    @log_and_propagate_error_on_service_method
    def get_user_account_by_username(self, username: str) -> UserAccountModel:
        """Returns a user account by its username.

        Args:
            username (str): The username of the account to retrieve.

        Returns:
            UserAccountModel: The requested user account.

        Raises:
            UserAccountUsernameNotFoundError: If no user account with the given username
                exists.
        """
        for user_account in self._user_accounts.values():
            if user_account.username == username:
                self._logger.debug("Retrieved user account: {!r}", user_account)
                return user_account
        raise UserAccountUsernameNotFoundError(username=username)

    @log_and_propagate_error_on_service_method
    def get_all_user_accounts(self) -> list[UserAccountModel]:
        """Returns all registered user accounts.

        Returns:
            list[UserAccountModel]: A list of all user accounts. Empty if none exist.
        """
        all_user_accounts = list(self._user_accounts.values())
        self._logger.debug(
            "Retrieved all user accounts ({} user account(s) retrieved)",
            len(all_user_accounts),
        )
        return all_user_accounts

    @log_and_propagate_error_on_service_method
    def create_user_account(
        self,
        username: str,
        password: str,
        role: str,
    ) -> UserAccountModel:
        """Creates a new user account and adds it to the in-memory registry.

        Args:
            username (str): The username for the new account. Must be non-empty and
                unique.
            password (str): The password for the new account. Must be non-empty.
            role (str): The role to assign to the new account.

        Returns:
            UserAccountModel: The newly created user account.

        Raises:
            EmptyUserAccountUsernameError: If `username` is empty.
            EmptyUserAccountPasswordError: If `password` is empty.
            InvalidUserAccountRoleError: If `role` is not a valid user role value.
            UserAccountUsernameAlreadyExistsError: If an account with the given username
                already exists.
        """
        if not username:
            raise EmptyUserAccountUsernameError._during_user_account_creation()
        if not password:
            raise EmptyUserAccountPasswordError._during_user_account_creation()
        if role not in self._authorization_service.get_all_roles():
            raise InvalidUserAccountRoleError._during_user_account_creation(role=role)
        for user_account in self.get_all_user_accounts():
            if user_account.username == username:
                raise UserAccountUsernameAlreadyExistsError._during_user_account_creation(
                    username=username,
                )

        user_account = UserAccountModel(
            username=username,
            password=password,
            role=role,
        )
        self._user_accounts[str(user_account.user_account_id)] = user_account
        self._logger.info("Created new user account: {}", user_account)

        return user_account

    @log_and_propagate_error_on_service_method
    def update_user_account_by_user_account_id(
        self,
        user_account_id: str | uuid.UUID,
        username: str | None = None,
        password: str | None = None,
        role: str | None = None,
    ) -> UserAccountModel:
        """Updates a user account's username, password, and/or role.

        Only fields that are not `None` are updated.

        Args:
            user_account_id (str | uuid.UUID): The ID of the user account to update.
            username (str | None): The new username. When `None`, the username is not
                changed.
            password (str | None): The new password. When `None`, the password is not
                changed.
            role (str | None): The new role. When `None`, the role is not changed.

        Returns:
            UserAccountModel: The updated user account.

        Raises:
            UserAccountIDNotFoundError: If no user account with the given ID exists.
            EmptyUserAccountUsernameError: If `username` is an empty string.
            EmptyUserAccountPasswordError: If `password` is an empty string.
            InvalidUserAccountRoleError: If `role` is not a valid user role value.
            UserAccountUsernameAlreadyExistsError: If an account with the given username
                already exists.
        """
        # Calling the `get_user_account_by_user_account_id()` method will implicitly
        # check to see if the user account ID is valid.
        user_account = self.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )

        # TODO: Check for no ops and also add event firing
        if username is not None:
            if not username:
                raise EmptyUserAccountUsernameError._during_user_account_modification(
                    user_account_str=str(user_account),
                )
            for existing_user_account in self.get_all_user_accounts():
                if existing_user_account.username == username:
                    raise UserAccountUsernameAlreadyExistsError._during_user_account_modification(
                        username=username,
                        user_account_str=str(user_account),
                    )
            old_username = user_account.username
            user_account.username = username
            self._logger.info(
                "Updated username for user account {} from '{}' to '{}'",
                user_account,
                old_username,
                username,
            )
        if password is not None:
            if not password:
                raise EmptyUserAccountPasswordError._during_user_account_modification(
                    user_account_str=str(user_account),
                )
            old_password = user_account.password
            user_account.password = password
            self._logger.info(
                "Updated password for user account {} from '{}' to '{}'",
                user_account,
                old_password,
                password,
            )
        if role is not None:
            if role not in self._authorization_service.get_all_roles():
                raise InvalidUserAccountRoleError._during_user_account_modification(
                    role=role,
                    user_account_str=str(user_account),
                )
            old_role = user_account.role
            user_account.role = role
            self._logger.info(
                "Updated role for {} from '{}' to '{}'",
                user_account,
                old_role,
                role,
            )

        return user_account

    @log_and_propagate_error_on_service_method
    def delete_user_account_by_user_account_id(
        self,
        user_account_id: str | uuid.UUID,
    ) -> None:
        """Deletes a user account from the in-memory registry.

        Args:
            user_account_id (str | uuid.UUID): The ID of the user account to delete.

        Returns:
            None

        Raises:
            UserAccountIDNotFoundError: If no user account with the given ID exists.
        """
        user_account = self.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )
        deleted_user_account = self._user_accounts.pop(
            str(user_account.user_account_id)
        )
        self._logger.info("Deleted user account: {}", deleted_user_account)
        self._logger.debug("- {!r}", deleted_user_account)

    @log_and_propagate_error_on_service_method
    def authenticate_user_account_credentials(
        self,
        username: str,
        password: str,
    ) -> UserAccountModel:
        """Validates a username and password against registered user accounts.

        Args:
            username (str): The username to authenticate.
            password (str): The password to validate.

        Returns:
            UserAccountModel: The authenticated user account.

        Raises:
            UserAccountAuthenticationError: If the username does not exist or the
                password does not match.
        """
        existing_usernames = [
            user_account.username for user_account in self.get_all_user_accounts()
        ]
        try:
            user_account = self.get_user_account_by_username(username=username)
        except UserAccountUsernameNotFoundError:
            raise UserAccountAuthenticationError() from None
        if username not in existing_usernames or user_account.password != password:
            raise UserAccountAuthenticationError()

        self._logger.debug("Authenticated user account: {!r}", user_account)

        return user_account

    @log_and_propagate_error_on_service_method
    def load_user_accounts_from_user_accounts_file(
        self,
        user_accounts_filepath: Path,
    ) -> list[UserAccountModel]:
        """Reads user accounts from a JSON file and adds them to the in-memory registry.

        Delegates parsing to `read_user_accounts_from_user_accounts_file` and then
        registers each parsed account.

        Args:
            user_accounts_filepath (Path): Path to the JSON file to read accounts from.

        Returns:
            list[UserAccountModel]: The list of user accounts loaded from the file.

        Raises:
            UserAccountsFileNotFoundError: If the file does not exist.
            UserAccountsFilepathIsDirectoryError: If the path points to a directory.
            UserAccountsFileIsNotJSONError: If the file is not valid JSON.
            UserAccountsFileSchemaError: If the JSON does not follow the expected schema.
            UserAccountsFileReadAccessError: If the file cannot be read due to
                insufficient permissions.
            UserAccountUsernameAlreadyExistsError: If a username from the file conflicts
                with an already-registered account.
            UserAccountsFileContainsDuplicateUsernamesError: If the file itself contains
                duplicate usernames.
        """
        new_user_accounts = self.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_filepath,
        )
        for user_account in new_user_accounts:
            self._user_accounts[str(user_account.user_account_id)] = user_account
            self._logger.debug("Loaded user account: {!r}", user_account)
        return new_user_accounts

    @log_and_propagate_error_on_service_method
    def read_user_accounts_from_user_accounts_file(
        self,
        user_accounts_filepath: Path,
    ) -> list[UserAccountModel]:
        """Reads and validates user accounts from a JSON file without registering them.

        Validates the file path, JSON structure, and schema. Checks that usernames are
        unique against both existing registered accounts and entries within the file
        itself.

        Args:
            user_accounts_filepath (Path): Path to the JSON file to read accounts from.

        Returns:
            list[UserAccountModel]: The list of parsed user accounts.

        Raises:
            UserAccountsFileNotFoundError: If the file does not exist.
            UserAccountsFilepathIsDirectoryError: If the path points to a directory.
            UserAccountsFileIsNotJSONError: If the file is not valid JSON.
            UserAccountsFileSchemaError: If the JSON does not follow the expected schema.
            UserAccountsFileReadAccessError: If the file cannot be read due to
                insufficient permissions.
            UserAccountUsernameAlreadyExistsError: If a username from the file conflicts
                with an already-registered account.
            UserAccountsFileContainsDuplicateUsernamesError: If the file itself contains
                duplicate usernames.
        """
        user_accounts_file_json_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "minLength": 1},
                    "password": {"type": "string", "minLength": 1},
                    "role": {
                        "type": "string",
                        "enum": ["SPECTATOR", "ADMIN", "OPERATOR"],
                    },
                },
            },
        }

        if not user_accounts_filepath.exists():
            raise UserAccountsFileNotFoundError(
                user_accounts_filepath=str(user_accounts_filepath),
            )
        if user_accounts_filepath.is_dir():
            raise UserAccountsFilepathIsDirectoryError(
                user_accounts_filepath=str(user_accounts_filepath),
            )
        try:
            self._logger.debug("Reading user accounts from: {}", user_accounts_filepath)
            with user_accounts_filepath.open("r") as file:
                data = file.read()
            json_data = json.loads(data)
            jsonschema.validate(
                instance=json_data,
                schema=user_accounts_file_json_schema,
            )
        except jsonschema.ValidationError as exc:
            raise UserAccountsFileSchemaError(
                user_accounts_filepath=str(user_accounts_filepath),
                json_schema_error_message=exc.message,
            ) from None
        except json.JSONDecodeError:
            raise UserAccountsFileIsNotJSONError(
                user_accounts_filepath=str(user_accounts_filepath),
            ) from None
        except PermissionError:
            raise UserAccountsFileReadAccessError(
                user_accounts_filepath=str(user_accounts_filepath),
            ) from None

        existing_usernames = [
            user_account.username for user_account in self.get_all_user_accounts()
        ]
        new_usernames = []
        new_user_accounts = []
        for user_account_json_data in json_data:
            # The JSON schema guarantees that the usernames and passwords are not empty
            # strings, so we do not need to check for that condition here.
            new_user_account = UserAccountModel(**user_account_json_data)
            if new_user_account.username in existing_usernames:
                raise UserAccountUsernameAlreadyExistsError._during_user_accounts_file_loading(
                    username=new_user_account.username,
                    user_accounts_filepath=str(user_accounts_filepath),
                )
            if new_user_account.username in new_usernames:
                raise UserAccountsFileContainsDuplicateUsernamesError(
                    user_accounts_filepath=user_accounts_filepath,
                    duplicate_username=new_user_account.username,
                )
            self._logger.debug("Read user account: {}", new_user_account)
            new_user_accounts.append(new_user_account)

        self._logger.debug(
            "Read user accounts from user accounts file ({} user account(s) read)",
            len(new_user_accounts),
        )
        return new_user_accounts

    @log_and_propagate_error_on_service_method
    def write_user_accounts_to_user_accounts_file(
        self,
        user_accounts_filepath: Path,
    ) -> int:
        """Serializes and writes all registered user accounts to a JSON file.

        Args:
            user_accounts_filepath (Path): Path to the file to write accounts to.

        Returns:
            int: The number of bytes written.

        Raises:
            UserAccountsFilepathIsDirectoryError: If the path points to a directory.
            UserAccountsFileWriteAccessError: If the file cannot be written due to
                insufficient permissions.
        """
        if user_accounts_filepath.is_dir():
            raise UserAccountsFilepathIsDirectoryError(
                user_accounts_filepath=str(user_accounts_filepath),
            )

        self._logger.debug("Writing user accounts to: {}", user_accounts_filepath)

        serializable_user_accounts = []
        for user_account in self.get_all_user_accounts():
            self._logger.debug("Writing user account: {}", user_account)
            serializable_user_accounts.append(
                {
                    "username": user_account.username,
                    "password": user_account.password,
                    "role": user_account.role,
                },
            )

        try:
            with user_accounts_filepath.open("w") as file:
                # Data is guaranteed to be JSON serializable at this point.
                data = json.dumps(serializable_user_accounts, indent=4)
                number_of_bytes_written = file.write(data)
        except PermissionError:
            raise UserAccountsFileWriteAccessError(
                user_accounts_filepath=str(user_accounts_filepath),
            ) from None

        self._logger.debug(
            "Wrote user accounts to user accounts file ({} byte(s) written)",
            number_of_bytes_written,
        )
        return number_of_bytes_written

    @log_and_propagate_error_on_service_method
    def load_framework_user_accounts(self) -> bool:
        """Loads user accounts from the framework's configured user accounts file.

        Errors encountered while loading are logged and suppressed; callers receive
        a boolean indicating success or failure.

        Returns:
            bool: `True` if accounts were loaded successfully, `False` if a
                `UserAccountsServiceError` occurred.
        """
        self._logger.debug("Loading framework user accounts...")

        try:
            loaded_user_accounts = self.load_user_accounts_from_user_accounts_file(
                user_accounts_filepath=self._user_accounts_json_file,
            )
        except UserAccountsServiceError as exc:
            self._logger.error(exc)
            return False

        for user_account in loaded_user_accounts:
            self._logger.debug("Loaded user account: {}", user_account)
        self._logger.debug(
            "Loaded framework user accounts ({} user account(s) loaded)",
            len(loaded_user_accounts),
        )
        return True

    @log_and_propagate_error_on_service_method
    def reload_framework_user_accounts(self) -> bool:
        """Deletes all existing user accounts then reloads them from the framework's file.

        Errors encountered while reloading are logged and suppressed; callers receive a
        boolean indicating success or failure.

        Returns:
            bool: `True` if accounts were reloaded successfully, `False` if a
                `UserAccountsServiceError` occurred.
        """
        self._logger.debug("Reloading framework user accounts...")

        try:
            for user_account_id in list(self._user_accounts.keys()):
                self.delete_user_account_by_user_account_id(
                    user_account_id=user_account_id,
                )
            loaded_user_accounts = self.load_user_accounts_from_user_accounts_file(
                user_accounts_filepath=self._user_accounts_json_file,
            )
        except UserAccountsServiceError as exc:
            self._logger.error("{}: {}", exc.__class__.__name__, exc)
            return False

        for user_account in loaded_user_accounts:
            self._logger.debug("Reloaded user account: {}", user_account)
        self._logger.debug(
            "Reloaded framework user accounts ({} user account(s) reloaded)",
            len(loaded_user_accounts),
        )
        return True

    @log_and_propagate_error_on_service_method
    def write_framework_user_accounts(self) -> bool:
        """Writes all in-memory user accounts to the framework's configured user accounts file.

        Errors encountered while writing are logged and suppressed; callers receive a
        boolean indicating success or failure.

        Returns:
            bool: `True` if accounts were written successfully, `False` if a
                `UserAccountsServiceError` occurred.
        """
        self._logger.debug("Writing framework user accounts...")

        try:
            number_of_bytes_written = self.write_user_accounts_to_user_accounts_file(
                user_accounts_filepath=self._user_accounts_json_file,
            )
        except UserAccountsServiceError as exc:
            self._logger.error(exc)
            return False

        for user_account in self.get_all_user_accounts():
            self._logger.debug(
                "Wrote user account: {!r}",
                user_account,
            )
        self._logger.debug(
            "Wrote framework user accounts ({} byte(s) written)",
            number_of_bytes_written,
        )
        return True
