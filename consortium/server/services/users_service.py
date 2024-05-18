from loguru import logger

from consortium.server.objects.user_objects import User


class UsersService:
    def __init__(self) -> None:
        self._users = {}
        self.users_service_logger = logger.bind(logger_name=str(self))
        self.users_service_logger.debug(f"Started {self}")

    def add_user(self, user: User) -> None:
        if str(user.user_id) in self._users:
            raise ValueError(
                f"Cannot add user to service because a user with the same user ID "
                f"already exists: {user.user_id}",
            )

        self._users[str(user.user_id)] = user
        self.users_service_logger.debug(f"Added user: {user!r}")
        self.users_service_logger.info(f"User logged in: {user}")

    def get_user_by_user_id(self, user_id: str) -> User:
        try:
            user = self._users[user_id]
        except KeyError:
            raise ValueError(f"No user exists with the provided user ID: {user_id}")

        self.users_service_logger.debug(f"Retrieved user: {user!r}")
        return user

    def get_user_by_access_token(self, access_token: str) -> User:
        for user in self._users.values():
            if str(user.json_web_token.subject) == access_token:
                self.users_service_logger.debug(f"Retrieved user: {user!r}")
                return user
        raise ValueError(
            f"No user exists with the provided access token: {access_token}",
        )

    def get_all_users(self) -> list[User]:
        all_users = list(self._users.values())
        self.users_service_logger.debug(
            f"Retrieved all users ({len(all_users)} retrieved).",
        )
        return all_users

    def remove_user(self, user: User) -> None:
        try:
            del [self._users[str(user.user_id)]]
        except KeyError:
            raise ValueError(f"User does not exist: {user}")

        self.users_service_logger.debug(f"Removed user: {user!r}")
        self.users_service_logger.info(f"User logged out: {user}")

    def __str__(self) -> str:
        return "Consortium Users Service"

    def __repr__(self) -> str:
        return "UsersService()"
