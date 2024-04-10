import json
from pathlib import Path

from loguru import logger
from pydantic import ValidationError

from consortium.server.models.user_account_models import UserAccountModel
from consortium.server.objects.user_account_objects import UserRole
from consortium.server.server_config import CONSORTIUM_USER_ACCOUNTS_JSON_FILE_PATH
from consortium.server.server_exceptions import (
    DuplicateUsernamesError,
    InvalidUserAccountError,
    InvalidUserAccountsFileError,
    UserAccountsFileNotFoundError,
)


class UserAccountsService:
    def __init__(self):
        # For brevity's sake, the representation of user accounts in the JSON file is as
        # a list of elements where each element is a unique user account (with a unique
        # username). To make accessing user accounts easier however, we use a dictionary
        # representation in the service internally
        self._user_accounts = {}
        self._user_accounts_service_logger = logger.bind(
            logger_name="Consortium User Accounts Service",
        )

        try:
            user_accounts = self._load_user_accounts_from_user_accounts_file(
                CONSORTIUM_USER_ACCOUNTS_JSON_FILE_PATH,
            )
            for user_account in user_accounts:
                self._user_accounts[str(user_account.user_account_id)] = user_account
                self._user_accounts_service_logger.debug(
                    f"Loaded user account: {user_account!r}",
                )
                self._user_accounts_service_logger.info(
                    f"Loaded user account: {user_account}",
                )
        except (
            UserAccountsFileNotFoundError,
            InvalidUserAccountsFileError,
            DuplicateUsernamesError,
            UserAccountsFileNotFoundError,
        ) as exc:
            self._user_accounts_service_logger.error(
                f"Failed to load user accounts. {exc}",
            )

    def _load_user_accounts_from_user_accounts_file(
        self,
        user_accounts_file: Path,
    ) -> list[UserAccountModel]:
        if not user_accounts_file.exists():
            raise UserAccountsFileNotFoundError(
                f"User accounts file not found: {user_accounts_file}",
            )

        try:
            user_accounts = []
            with user_accounts_file.open("r") as file:
                data = file.read()
                json_data = json.loads(data)
                for user_account_json_data in json_data:
                    user_account = UserAccountModel(**user_account_json_data)
                    if user_account.username in self._user_accounts:
                        raise DuplicateUsernamesError(
                            f"Duplicate username {user_account.username} detected in user accounts file: {user_accounts_file}",
                        )
                    user_accounts.append(user_account)
            return user_accounts
        except json.JSONDecodeError as exc:
            raise InvalidUserAccountsFileError(
                f"Invalid JSON data in user accounts file {user_accounts_file}: {exc}",
            )
        except ValidationError as exc:
            raise InvalidUserAccountError(
                f"Invalid user account data in user accounts file {user_accounts_file}: {exc}",
            )

    def _write_user_accounts_to_user_accounts_file(self):
        serializable_user_accounts = [
            {
                "username": user_account.username,
                "password": user_account.password,
                "role": user_account.role.value,
            }
            for user_account in self._user_accounts.values()
        ]

        with open("data/server/user_accounts.json", "w") as file:
            data = json.dumps(serializable_user_accounts, indent=4)
            file.write(data)
        self._user_accounts_service_logger.debug(
            f"Wrote user accounts to user accounts file ({len(data)} bytes written).",
        )

    def create_user_account(
        self,
        username: str,
        password: str,
        role: UserRole,
    ) -> UserAccountModel:
        # A ValueError is expressly raised here because the provided value is invalid.
        # Compare this to a KeyError in the other methods which is raised when an
        # attempt to access a value is invalid rather than an attempt to create a value
        for user_account in self._user_accounts.values():
            if user_account.username == username:
                raise ValueError(
                    f"User accounts with duplicate username are not allowed: {username}",
                )

        user_account = UserAccountModel(
            username=username,
            password=password,
            role=role,
        )
        self._user_accounts[str(user_account.user_account_id)] = user_account
        self._user_accounts_service_logger.info(f"Created user account: {user_account}")
        self._write_user_accounts_to_user_accounts_file()

        return user_account

    def get_user_account_by_user_account_id(
        self,
        user_account_id: str,
    ) -> UserAccountModel:
        try:
            user_account = self._user_accounts[user_account_id]
        except KeyError:
            raise ValueError(
                f"No user account has the provided user account ID: {user_account_id}",
            )

        self._user_accounts_service_logger.debug(
            f"Retrieved user account: {user_account!r}",
        )
        return user_account

    def get_user_account_by_username(self, username: str) -> UserAccountModel:
        for user_account in self._user_accounts.values():
            if user_account.username == username:
                self._user_accounts_service_logger.debug(
                    f"Retrieved user account: {user_account!r}",
                )
                return user_account
        raise ValueError(f"No user account has the provided username: {username}")

    def get_all_user_accounts(self) -> list[UserAccountModel]:
        all_user_accounts = list(self._user_accounts.values())
        self._user_accounts_service_logger.debug(
            f"Retrieved all user accounts ({len(all_user_accounts)} retrieved).",
        )
        return all_user_accounts

    def update_user_account_password(
        self,
        user_account: UserAccountModel,
        password: str,
    ) -> None:
        # We perform a LBYL over EAFP check here because accessing the dictionary is
        # not necessary since the user_account object is a reference to the object in
        # the dictionary. Otherwise, given that we will access the dictionary, we would
        # use a try-except block to EAFP.
        if user_account not in self._user_accounts.values():
            raise ValueError(
                f"User account does not exist: {user_account}",
            )

        # We don't need to explicitly update the self._user_accounts dictionary because
        # the user_account object is a reference to the object in the dictionary.
        old_password = user_account.password
        user_account.password = password
        self._user_accounts_service_logger.debug(
            f"Updated password for {user_account!r}: {old_password} -> {password}",
        )
        self._user_accounts_service_logger.info(
            f"Updated password for {user_account}: {old_password} -> {password}",
        )
        self._write_user_accounts_to_user_accounts_file()

    def update_user_account_role(
        self,
        user_account: UserAccountModel,
        role: UserRole,
    ) -> None:
        if user_account not in self._user_accounts.values():
            raise ValueError(
                f"User account does not exist: {user_account}",
            )

        old_role = user_account.role
        user_account.role = role
        self._user_accounts_service_logger.debug(
            f"Updated role for {user_account!r}: {old_role} -> {role}",
        )
        self._user_accounts_service_logger.info(
            f"Updated role for {user_account}: {old_role} -> {role}",
        )
        self._write_user_accounts_to_user_accounts_file()

    def delete_user_account(self, user_account: UserAccountModel) -> None:
        try:
            del self._user_accounts[str(user_account.user_account_id)]
        except KeyError:
            raise ValueError(
                f"User account does not exist: {user_account}",
            )

        self._user_accounts_service_logger.debug(
            f"Deleted user account: {user_account!r}",
        )
        self._user_accounts_service_logger.info(
            f"Deleted user account: {user_account}",
        )
        self._write_user_accounts_to_user_accounts_file()
