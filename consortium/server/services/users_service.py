from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.service_exceptions.users_service_exceptions import (
    UserAccessTokenNotFoundError,
    UserIDNotFoundError,
)
from consortium.server.objects.user_objects import User


class UsersService:
    def __init__(self) -> None:
        self._users = {}
        self._logger = logger.bind(logger_name=str(self))
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Users Service"

    def __repr__(self) -> str:
        return "UsersService()"

    def get_user_by_user_id(self, user_id: str) -> User:
        try:
            user = self._users[user_id]
        except KeyError:
            raise UserIDNotFoundError(user_id=user_id) from None

        self._logger.debug("Retrieved user: {!r}", user)
        return user

    def get_user_by_access_token(self, access_token: str) -> User:
        for user in self.get_all_users():
            if str(user.json_web_token.subject) == access_token:
                self._logger.debug("Retrieved user: {!r}", user)
                return user
        raise UserAccessTokenNotFoundError(access_token=access_token)

    def get_all_users(self) -> list[User]:
        all_users = list(self._users.values())
        self._logger.debug(
            "Retrieved all users ({} user(s) retrieved).",
            len(all_users),
        )
        return all_users

    def update_user_display_name_by_user_id(
        self,
        display_name: str,
        user_id: str,
    ) -> User:
        user = self.get_user_by_user_id(user_id=user_id)
        old_display_name = user.display_name
        user.display_name = display_name
        self._logger.info(
            "Updated user display name for {}: '{}' -> '{}'",
            user,
            old_display_name,
            display_name,
        )
        return user

    def login_user(self, username: str, password: str) -> User:
        user_account = server_singletons.user_accounts_service.authenticate_user_account_credentials(
            username=username,
            password=password,
        )
        user = User(user_account=user_account)
        self._users[str(user.user_id)] = user

        self._logger.info("User logged in: {}", user)
        self._logger.debug("- {!r}", user)
        return user

    def logout_user_by_user_id(self, user_id: str) -> None:
        try:
            deleted_user = self._users.pop(str(user_id))
        except KeyError:
            raise UserIDNotFoundError(user_id=user_id) from None

        self._logger.info("User logged out: {}", deleted_user)
        self._logger.debug("- {!r}", deleted_user)
