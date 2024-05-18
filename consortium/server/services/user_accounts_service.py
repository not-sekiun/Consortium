import json
from pathlib import Path

from loguru import logger
from pydantic import ValidationError

from consortium.server.exceptions.internal_server_exceptions import (
    DuplicateUserAccountUsernamesError,
    InvalidUserAccountError,
    InvalidUserAccountsFileError,
    UserAccountsFileNotFoundError,
)
from consortium.server.models.user_account_models import UserAccountModel
from consortium.server.objects.user_account_objects import UserRole
from consortium.server.server_config import CONSORTIUM_USER_ACCOUNTS_JSON_FILE_PATH


# TODO: Redo, add more methods, consider transitioning to using ID
class UserAccountsService:
    def __init__(self):
        # For brevity's sake, the representation of user accounts in the JSON file is as
        # a list of elements where each element is a unique user account (with a unique
        # username). To make accessing user accounts easier however, we use a dictionary
        # representation in the service internally
        self._user_accounts = {}
        self.user_accounts_service_logger = logger.bind(
            logger_name=str(self),
        )
        self.user_accounts_service_logger.debug(
            f"Started {self}",
        )

    def __str__(self) -> str:
        return "Consortium User Accounts Service"

    def __repr__(self) -> str:
        return "UserAccountsService()"

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
        self.user_accounts_service_logger.debug(
            f"Retrieved user account: {user_account!r}",
        )
        return user_account

    def get_user_account_by_username(self, username: str) -> UserAccountModel:
        for user_account in self._user_accounts.values():
            if user_account.username == username:
                self.user_accounts_service_logger.debug(
                    f"Retrieved user account: {user_account!r}",
                )
                return user_account
        raise ValueError(f"No user account has the provided username: {username}")

    def get_all_user_accounts(self) -> list[UserAccountModel]:
        all_user_accounts = list(self._user_accounts.values())
        self.user_accounts_service_logger.debug(
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
        for user_account in self._user_accounts.values():
            if user_account.username == username:
                raise ValueError(
                    f"User accounts with duplicate usernames are not allowed: "
                    f"{username}",
                )

        user_account = UserAccountModel(
            username=username,
            password=password,
            role=role,
        )
        self._user_accounts[str(user_account.user_account_id)] = user_account
        self.user_accounts_service_logger.info(f"Created user account: {user_account}")

        return user_account

    def update_user_account_username_by_user_account_id(
        self,
        user_account_id: str,
        new_username: str,
    ) -> UserAccountModel:
        user_account = self.get_user_account_by_user_account_id(user_account_id)

        for existing_user_account in self._user_accounts.values():
            if existing_user_account.username == new_username:
                raise ValueError(
                    f"User accounts with duplicate usernames are not allowed: "
                    f"{new_username}",
                )

        # Modifying the user account here will modify its entry within the user accounts
        # dictionary.
        old_username = user_account.username
        user_account.username = new_username
        self.user_accounts_service_logger.debug(
            f"Updated username for user account {user_account!r}: {old_username} -> "
            f"{new_username}",
        )

        return user_account

    def update_user_account_password_by_user_account_id(
        self,
        user_account_id: str,
        new_password: str,
    ) -> UserAccountModel:
        user_account = self.get_user_account_by_user_account_id(user_account_id)

        # Modifying the user account here will modify its entry within the user accounts
        # dictionary.
        old_password = user_account.password
        user_account.password = new_password
        self.user_accounts_service_logger.debug(
            f"Updated password for user account {user_account!r}: {old_password} -> "
            f"{new_password}",
        )

        return user_account

    def update_user_account_role_by_user_account_id(
        self,
        user_account_id: str,
        new_role: UserRole,
    ) -> UserAccountModel:
        user_account = self.get_user_account_by_user_account_id(user_account_id)

        # Modifying the user account here will modify its entry within the user accounts
        # dictionary.
        old_role = user_account.role
        user_account.role = new_role
        self.user_accounts_service_logger.info(
            f"Updated role for {user_account}: {old_role} -> {new_role}",
        )

        return user_account

    def delete_user_account_by_user_account_id(
        self,
        user_account_id: str,
    ) -> None:
        # Check to see if the user account exists. If it does not exist, a ValueError
        # is automatically raised from the get_user_account_by_user_account_id method.
        _ = self.get_user_account_by_user_account_id(user_account_id)

        deleted_user_account = self._user_accounts.pop(str(user_account_id))
        self.user_accounts_service_logger.info(
            f"Deleted user account: {deleted_user_account}",
        )

    def load_framework_user_accounts(self) -> None:
        try:
            user_accounts = self.get_user_accounts_from_user_accounts_file(
                CONSORTIUM_USER_ACCOUNTS_JSON_FILE_PATH,
            )
            for user_account in user_accounts:
                self._user_accounts[str(user_account.user_account_id)] = user_account
                self.user_accounts_service_logger.debug(
                    f"Loaded user account: {user_account!r}",
                )
        except (
            UserAccountsFileNotFoundError,
            InvalidUserAccountsFileError,
            DuplicateUserAccountUsernamesError,
            UserAccountsFileNotFoundError,
        ) as exc:
            self.user_accounts_service_logger.error(
                f"Failed to load user accounts. {exc}",
            )

    def reload_framework_user_accounts(self) -> None:
        self.user_accounts_service_logger.info("Reloading framework user accounts...")
        self._user_accounts.clear()
        self.load_framework_user_accounts()
        self.user_accounts_service_logger.info("Reloaded framework user accounts.")

    def write_framework_user_accounts(self):
        self.user_accounts_service_logger.info("Writing framework user accounts...")
        self.write_user_accounts_to_user_accounts_file(
            CONSORTIUM_USER_ACCOUNTS_JSON_FILE_PATH,
        )
        self.user_accounts_service_logger.info(f"Wrote framework user accounts.")

    def get_user_accounts_from_user_accounts_file(
        self,
        user_accounts_filepath: Path,
    ) -> list[UserAccountModel]:
        if not user_accounts_filepath.exists():
            raise UserAccountsFileNotFoundError(
                f"User accounts file not found: {user_accounts_filepath}",
            )

        try:
            user_accounts = []
            with user_accounts_filepath.open("r") as file:
                data = file.read()
                json_data = json.loads(data)
                for user_account_json_data in json_data:
                    user_account = UserAccountModel(**user_account_json_data)
                    if user_account.username in self._user_accounts:
                        raise DuplicateUserAccountUsernamesError(
                            f"Duplicate username {user_account.username} detected in "
                            f"user accounts file: {user_accounts_filepath}",
                        )
                    user_accounts.append(user_account)
            return user_accounts
        except json.JSONDecodeError as exc:
            raise InvalidUserAccountsFileError(
                f"Invalid JSON data in user accounts file {user_accounts_filepath}: {exc}",
            )
        except ValidationError as exc:
            raise InvalidUserAccountError(
                f"Invalid user account data in user accounts file "
                f"{user_accounts_filepath}: {exc}",
            )

    def write_user_accounts_to_user_accounts_file(self, user_accounts_filepath: Path):
        serializable_user_accounts = [
            {
                "username": user_account.username,
                "password": user_account.password,
                "role": user_account.role.value,
            }
            for user_account in self._user_accounts.values()
        ]

        with user_accounts_filepath.open("w") as file:
            data = json.dumps(serializable_user_accounts, indent=4)
            file.write(data)
        self.user_accounts_service_logger.debug(
            f"Wrote user accounts to user accounts file ({len(data)} bytes written).",
        )
