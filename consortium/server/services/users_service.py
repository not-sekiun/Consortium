from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.server.exceptions.service_exceptions.users_service_exceptions import (
    InvalidAccessTokenServiceError,
    InvalidUserIDServiceError,
)
from consortium.server.objects.user_objects import User


class UsersService:
    def __init__(self) -> None:
        self._users = {}
        self.users_service_logger = logger.bind(logger_name=str(self))
        self.users_service_logger.debug(f"Started {self}")

    def __str__(self) -> str:
        return "Consortium Users Service"

    def __repr__(self) -> str:
        return "UsersService()"

    def get_user_by_user_id(self, user_id: str) -> User:
        try:
            user = self._users[user_id]
        except KeyError:
            raise InvalidUserIDServiceError(user_id=user_id)

        self.users_service_logger.debug(f"Retrieved user: {user!r}")
        return user

    def get_user_by_access_token(self, access_token: str) -> User:
        for user in self.get_all_users():
            if str(user.json_web_token.subject) == access_token:
                self.users_service_logger.debug(f"Retrieved user: {user!r}")
                return user
        raise InvalidAccessTokenServiceError(access_token=access_token)

    def get_all_users(self) -> list[User]:
        all_users = list(self._users.values())
        self.users_service_logger.debug(
            f"Retrieved all users ({len(all_users)} user(s) retrieved).",
        )
        return all_users

    def update_user_display_name_by_user_id(
        self,
        new_display_name: str,
        user_id: str,
    ) -> User:
        user = self.get_user_by_user_id(user_id=user_id)
        old_display_name = user.display_name
        user.display_name = new_display_name

        self.users_service_logger.info(
            f"Updated user display name for {user}: '{old_display_name}' -> "
            f"'{new_display_name}'",
        )
        return user

    def login_user(self, username: str, password: str) -> User:
        user_account = server_singletons.user_accounts_service.authenticate_user_account_credentials(
            username=username,
            password=password,
        )
        user = User(user_account=user_account)
        self._users[str(user.user_id)] = user

        self.users_service_logger.info(f"User logged in: {user}")
        self.users_service_logger.debug(f"Added user: {user!r}")
        return user

    def logout_user_by_user_id(self, user_id: str) -> None:
        try:
            deleted_user = self._users.pop(str(user_id))
        except KeyError:
            raise InvalidUserIDServiceError(user_id=user_id)

        self.users_service_logger.info(f"User logged out: {deleted_user}")
        self.users_service_logger.debug(f"Removed user: {deleted_user!r}")
