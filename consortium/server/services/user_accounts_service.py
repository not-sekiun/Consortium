import json
from pathlib import Path

import jsonschema
from loguru import logger

from consortium.server.exceptions.service_exceptions.user_accounts_service_exceptions import (
    EmptyUserAccountPasswordError,
    EmptyUserAccountUsernameError,
    IdenticalUserAccountPasswordError,
    IdenticalUserAccountRoleError,
    IdenticalUserAccountUsernameError,
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


class UserAccountsService:
    def __init__(self):
        self._user_accounts = {}
        self.logger = logger.bind(
            logger_name=str(self),
        )
        self.logger.debug(
            f"Started {self}",
        )

    def __str__(self) -> str:
        return "User Accounts Service"

    def __repr__(self) -> str:
        return "UserAccountsService()"

    def get_user_account_by_user_account_id(
        self,
        user_account_id: str,
    ) -> UserAccountModel:
        try:
            user_account = self._user_accounts[user_account_id]
        except KeyError:
            raise UserAccountIDNotFoundError(
                user_account_id=user_account_id,
            )
        self.logger.debug(
            f"Retrieved user account: {user_account!r}",
        )

        # Always return a deep copy of the user account to prevent the caller from
        # modifying the original user account by interacting with the instantiated user
        # account model directly.
        return user_account

    def get_user_account_by_username(self, username: str) -> UserAccountModel:
        for user_account in self._user_accounts.values():
            if user_account.username == username:
                self.logger.debug(
                    f"Retrieved user account: {user_account!r}",
                )
                return user_account

        raise UserAccountUsernameNotFoundError(username=username)

    def get_all_user_accounts(self) -> list[UserAccountModel]:
        all_user_accounts = list(self._user_accounts.values())
        self.logger.debug(
            f"Retrieved all user accounts ({len(all_user_accounts)} user account(s) "
            "retrieved).",
        )

        return all_user_accounts

    def create_user_account(
        self,
        username: str,
        password: str,
        role: UserRole,
    ) -> UserAccountModel:
        if not username:
            raise EmptyUserAccountUsernameError.during_user_account_creation()
        if not password:
            raise EmptyUserAccountPasswordError.during_user_account_creation()
        if role not in UserRole:
            raise InvalidUserAccountRoleError.during_user_account_creation(role=role)
        for user_account in self.get_all_user_accounts():
            if user_account.username == username:
                raise UserAccountUsernameAlreadyExistsError.during_user_account_creation(
                    username=username,
                )

        user_account = UserAccountModel(
            username=username,
            password=password,
            role=role,
        )
        self._user_accounts[str(user_account.user_account_id)] = user_account
        self.logger.info(
            f"Created new user account: {user_account}",
        )

        return user_account

    def update_user_account_username_by_user_account_id(
        self,
        user_account_id: str,
        username: str,
    ) -> UserAccountModel:
        # Calling the `get_user_account_by_user_account_id()` method will implicitly
        # check to see if the user account ID is valid. If not, an
        # InvalidUserAccountIDError will be thrown and propagated upwards to the
        # caller.
        user_account = self.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )

        if not username:
            raise EmptyUserAccountUsernameError.during_user_account_modification(
                user_account=str(user_account),
            )
        if user_account.username == username:
            raise IdenticalUserAccountUsernameError(
                username=username,
                user_account_str=str(user_account),
            )
        for existing_user_account in self.get_all_user_accounts():
            if existing_user_account.username == username:
                raise UserAccountUsernameAlreadyExistsError.during_user_account_modification(
                    username=username,
                    user_account=str(user_account),
                )

        old_username = user_account.username
        user_account.username = username
        self.logger.info(
            f"Updated username for user account {user_account}: '{old_username}' -> "
            f"'{username}'",
        )

        return user_account

    def update_user_account_password_by_user_account_id(
        self,
        user_account_id: str,
        password: str,
    ) -> UserAccountModel:
        user_account = self.get_user_account_by_user_account_id(
            user_account_id=user_account_id,
        )

        if not password:
            raise EmptyUserAccountPasswordError.during_user_account_modification(
                user_account=str(user_account),
            )
        if user_account.password == password:
            raise IdenticalUserAccountPasswordError

        old_password = user_account.password
        user_account.password = password
        self.logger.info(
            f"Updated password for user account {user_account}: '{old_password}' -> "
            f"'{password}'",
        )
        return user_account

    def update_user_account_role_by_user_account_id(
        self,
        user_account_id: str,
        role: UserRole,
    ) -> UserAccountModel:
        user_account = self.get_user_account_by_user_account_id(user_account_id)

        if role not in UserRole:
            raise InvalidUserAccountRoleError.during_user_account_modification(
                role=role,
                user_account=str(user_account),
            )
        if user_account.role == role:
            raise IdenticalUserAccountRoleError(
                user_account_str=str(user_account),
                role=role,
            )

        old_role = user_account.role
        user_account.role = role
        self.logger.info(
            f"Updated role for {user_account}: '{old_role}' -> '{role}'",
        )

        return user_account

    def delete_user_account_by_user_account_id(
        self,
        user_account_id: str,
    ) -> None:
        try:
            deleted_user_account = self._user_accounts.pop(str(user_account_id))
        except KeyError:
            raise UserAccountIDNotFoundError(user_account_id=user_account_id)
        self.logger.info(
            f"Deleted user account: {deleted_user_account}",
        )

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
            raise UserAccountAuthenticationError
        if username not in existing_usernames:
            raise UserAccountAuthenticationError
        if user_account.password != password:
            raise UserAccountAuthenticationError

        self.logger.debug(
            f"Authenticated user account: {user_account!r}",
        )

        return user_account

    def load_user_accounts_from_user_accounts_file(
        self,
        user_accounts_filepath: Path,
    ) -> list[UserAccountModel]:
        new_user_accounts = self.read_user_accounts_from_user_accounts_file(
            user_accounts_filepath=user_accounts_filepath,
        )
        for user_account in new_user_accounts:
            self._user_accounts[str(user_account.user_account_id)] = user_account
            self.logger.debug(
                f"Loaded user account: {user_account!r}",
            )
        return new_user_accounts

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
            )
        except json.JSONDecodeError:
            raise UserAccountsFileIsNotJSONError(
                user_accounts_filepath=str(user_accounts_filepath),
            )
        except PermissionError:
            raise UserAccountsFileReadAccessError(
                user_accounts_filepath=str(user_accounts_filepath),
            )

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
                raise UserAccountUsernameAlreadyExistsError.during_user_accounts_file_loading(
                    username=new_user_account.username,
                    user_accounts_filepath=str(user_accounts_filepath),
                )
            if new_user_account.username in new_usernames:
                raise UserAccountsFileContainsDuplicateUsernamesError(
                    user_accounts_filepath=user_accounts_filepath,
                    duplicate_username=new_user_account.username,
                )
            self.logger.debug(
                f"Read user account: {new_user_account}",
            )
            new_user_accounts.append(new_user_account)

        self.logger.debug(
            f"Read user accounts from user accounts file ({len(new_user_accounts)} "
            "user account(s) read).",
        )
        return new_user_accounts

    def write_user_accounts_to_user_accounts_file(
        self,
        user_accounts_filepath: Path,
    ) -> int:
        if user_accounts_filepath.is_dir():
            raise UserAccountsFilepathIsDirectoryError(
                user_accounts_filepath=str(user_accounts_filepath),
            )

        serializable_user_accounts = []

        for user_account in self.get_all_user_accounts():
            self.logger.debug(
                f"Writing user account: {user_account}",
            )
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
            )

        self.logger.debug(
            f"Wrote user accounts to user accounts file ({number_of_bytes_written} "
            f"byte(s) written).",
        )
        return number_of_bytes_written

    def load_framework_user_accounts(self) -> bool:
        self.logger.debug("Loading framework user accounts...")

        try:
            loaded_user_accounts = self.load_user_accounts_from_user_accounts_file(
                user_accounts_filepath=CONSORTIUM_USER_ACCOUNTS_JSON_FILE_PATH,
            )
        except UserAccountsServiceError as exc:
            self.logger.error(exc)
            return False

        for user_account in loaded_user_accounts:
            self.logger.debug(
                f"Loaded user account: {user_account}",
            )
        self.logger.debug(
            f"Loaded framework user accounts ({len(loaded_user_accounts)} user "
            f"account(s) loaded).",
        )
        return True

    def reload_framework_user_accounts(self) -> bool:
        self.logger.debug("Reloading framework user accounts...")

        try:
            for user_account_id in list(self._user_accounts.keys()):
                self.delete_user_account_by_user_account_id(
                    user_account_id=user_account_id,
                )
            loaded_user_accounts = self.load_user_accounts_from_user_accounts_file(
                user_accounts_filepath=CONSORTIUM_USER_ACCOUNTS_JSON_FILE_PATH,
            )
        except UserAccountsServiceError as exc:
            self.logger.error(f"{exc.__class__.__name__}: {exc}")
            return False

        for user_account in loaded_user_accounts:
            self.logger.debug(
                f"Reloaded user account: {user_account}",
            )
        self.logger.debug(
            f"Reloaded framework user accounts ({len(loaded_user_accounts)} user "
            f"account(s) reloaded).",
        )
        return True

    def write_framework_user_accounts(self) -> bool:
        self.logger.debug("Writing framework user accounts...")

        try:
            number_of_bytes_written = self.write_user_accounts_to_user_accounts_file(
                user_accounts_filepath=CONSORTIUM_USER_ACCOUNTS_JSON_FILE_PATH,
            )
        except UserAccountsServiceError as exc:
            self.logger.error(exc)
            return False

        for user_account in self.get_all_user_accounts():
            self.logger.debug(
                f"Wrote user account: {user_account}",
            )
        self.logger.debug(
            f"Wrote framework user accounts ({number_of_bytes_written} byte(s) "
            f"written).",
        )
        return True
