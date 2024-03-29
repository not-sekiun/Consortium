import json

from loguru import logger

from consortium.server.models.user_account_models import UserAccountModel
from consortium.server.objects.user_account_objects import UserRole


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

        with open("data/server/user_accounts.json", "r") as f:
            data = f.read()
            json_data = json.loads(data)
            for user_account_json_data in json_data:
                user_account = UserAccountModel(**user_account_json_data)
                if user_account.username in self._user_accounts:
                    # TODO: Figure out a cleaner way to deal with configuration
                    #  type errors at start up
                    raise ValueError("User accounts must have unique usernames")
                self._user_accounts[str(user_account.user_account_id)] = user_account
                self._user_accounts_service_logger.debug(
                    f'Loaded user account: "{user_account.username}" ({user_account.user_account_id})',
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
            f"Wrote user accounts to user accounts file ({len(data)} bytes written)",
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
                    f'User account with the username "{username}" already exists',
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
                f'User account with the user account ID "{user_account_id}" does not exist',
            )

        self._user_accounts_service_logger.debug(
            f'Retrieved user account "{user_account.username}" ({user_account_id})',
        )
        return user_account

    def get_user_account_by_username(self, username: str) -> UserAccountModel:
        for user_account in self._user_accounts.values():
            if user_account.username == username:
                self._user_accounts_service_logger.debug(
                    f'Retrieved user account "{user_account.username}" ({user_account.user_account_id})',
                )
                return user_account
        raise ValueError(f'User account with the username "{username}" does not exist')

    def get_all_user_accounts(self) -> list[UserAccountModel]:
        all_user_accounts = list(self._user_accounts.values())
        self._user_accounts_service_logger.debug(
            f"Retrieved all user accounts ({len(all_user_accounts)} retrieved)",
        )
        return all_user_accounts

    def update_user_account_password(
        self,
        user_account: UserAccountModel,
        password: str,
    ) -> None:
        # We perform a LBYL over EAFP check here because accessing the dictionary is
        # not necessary since the user_account object is a reference to the object in
        # the dictionary. Otherwise given that we will access the dictionary, we would
        # use a try-except block to EAFP.
        if user_account not in self._user_accounts.values():
            raise ValueError(
                f'User account "{user_account.username}" ({user_account.user_account_id}) does not exist',
            )

        # We don't need to explicitly update the self._user_accounts dictionary because
        # the user_account object is a reference to the object in the dictionary.
        user_account.password = password
        self._user_accounts_service_logger.info(
            f'Updated user account "{user_account.username}"\'s ({user_account.user_account_id}) password',
        )
        self._write_user_accounts_to_user_accounts_file()

    def update_user_account_role(
        self,
        user_account: UserAccountModel,
        role: UserRole,
    ) -> None:
        if user_account not in self._user_accounts.values():
            raise ValueError(
                f'User account "{user_account.username}" ({user_account.user_account_id}) does not exist',
            )

        user_account.role = role
        self._user_accounts_service_logger.info(
            f'Updated user account "{user_account.username}"\'s ({user_account.user_account_id}) role',
        )
        self._write_user_accounts_to_user_accounts_file()

    def delete_user_account(self, user_account: UserAccountModel) -> None:
        try:
            del self._user_accounts[str(user_account.user_account_id)]
        except KeyError:
            raise ValueError(
                f'User account "{user_account.username}" ({user_account.user_account_id}) does not exist',
            )

        self._user_accounts_service_logger.info(
            f'Deleted user account "{user_account.username}" ({user_account.user_account_id})',
        )
        self._write_user_accounts_to_user_accounts_file()
