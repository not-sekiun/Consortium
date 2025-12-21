import json
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
from consortium.server.models.user_account_models import UserAccountModel
from consortium.server.objects.user_account_objects import UserRole
from consortium.server.server_config import CONSORTIUM_USER_ACCOUNTS_JSON_FILE_PATH
from consortium.server.server_logging import LoggerType
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
)


class UserAccountsService:
    def __init__(self):
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
        for user_account in self._user_accounts.values():
            if user_account.username == username:
                self._logger.debug("Retrieved user account: {!r}", user_account)
                return user_account
        raise UserAccountUsernameNotFoundError(username=username)

    @log_and_propagate_error_on_service_method
    def get_all_user_accounts(self) -> list[UserAccountModel]:
        all_user_accounts = list(self._user_accounts.values())
        self._logger.debug(
            "Retrieved all user accounts ({} user account(s) retrieved).",
            len(all_user_accounts),
        )
        return all_user_accounts

    @log_and_propagate_error_on_service_method
    def create_user_account(
        self,
        username: str,
        password: str,
        role: UserRole,
    ) -> UserAccountModel:
        if not username:
            raise EmptyUserAccountUsernameError._during_user_account_creation()
        if not password:
            raise EmptyUserAccountPasswordError._during_user_account_creation()
        if role not in UserRole:
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
        role: UserRole | None = None,
    ) -> UserAccountModel:
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
            if role not in UserRole:
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
            "Read user accounts from user accounts file ({} user account(s) read).",
            len(new_user_accounts),
        )
        return new_user_accounts

    @log_and_propagate_error_on_service_method
    def write_user_accounts_to_user_accounts_file(
        self,
        user_accounts_filepath: Path,
    ) -> int:
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
                    "role": user_account.role.value,
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
            "Wrote user accounts to user accounts file ({} byte(s) written).",
            number_of_bytes_written,
        )
        return number_of_bytes_written

    @log_and_propagate_error_on_service_method
    def load_framework_user_accounts(self) -> bool:
        self._logger.debug("Loading framework user accounts...")

        try:
            loaded_user_accounts = self.load_user_accounts_from_user_accounts_file(
                user_accounts_filepath=CONSORTIUM_USER_ACCOUNTS_JSON_FILE_PATH,
            )
        except UserAccountsServiceError as exc:
            self._logger.error(exc)
            return False

        for user_account in loaded_user_accounts:
            self._logger.debug("Loaded user account: {}", user_account)
        self._logger.debug(
            "Loaded framework user accounts ({} user account(s) loaded).",
            len(loaded_user_accounts),
        )
        return True

    @log_and_propagate_error_on_service_method
    def reload_framework_user_accounts(self) -> bool:
        self._logger.debug("Reloading framework user accounts...")

        try:
            for user_account_id in list(self._user_accounts.keys()):
                self.delete_user_account_by_user_account_id(
                    user_account_id=user_account_id,
                )
            loaded_user_accounts = self.load_user_accounts_from_user_accounts_file(
                user_accounts_filepath=CONSORTIUM_USER_ACCOUNTS_JSON_FILE_PATH,
            )
        except UserAccountsServiceError as exc:
            self._logger.error("{}: {}", exc.__class__.__name__, exc)
            return False

        for user_account in loaded_user_accounts:
            self._logger.debug("Reloaded user account: {}", user_account)
        self._logger.debug(
            "Reloaded framework user accounts ({} user account(s) reloaded).",
            len(loaded_user_accounts),
        )
        return True

    @log_and_propagate_error_on_service_method
    def write_framework_user_accounts(self) -> bool:
        self._logger.debug("Writing framework user accounts...")

        try:
            number_of_bytes_written = self.write_user_accounts_to_user_accounts_file(
                user_accounts_filepath=CONSORTIUM_USER_ACCOUNTS_JSON_FILE_PATH,
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
            "Wrote framework user accounts ({} byte(s) written).",
            number_of_bytes_written,
        )
        return True
