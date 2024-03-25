from loguru import logger

from consortium.server.objects.user_objects import User


class UsersService:
    def __init__(self) -> None:
        self._users = {}
        self._users_service_logger = logger.bind(logger_name="Consortium Users Service")

    def add_user(self, user: User) -> None:
        self._users[str(user.user_id)] = user
        self._users_service_logger.info(
            f'User "{user.username}" ({user.user_id}) logged in',
        )

    def get_user_by_user_id(self, user_id: str) -> User:
        try:
            return self._users[user_id]
        except KeyError:
            raise ValueError(f'User with the user ID "{user_id}" does not exist')

    def get_user_by_access_token(self, access_token: str) -> User:
        for user in self._users.values():
            if str(user.json_web_token.subject) == access_token:
                return user
        raise ValueError("No user has the provided access token")

    def get_all_users(self) -> list[User]:
        return list(self._users.values())

    def remove_user(self, user: User) -> None:
        try:
            del [self._users[str(user.user_id)]]
        except KeyError:
            raise ValueError(f'User with the user ID "{user.user_id}" does not exist')
        self._users_service_logger.info(
            f'User "{user.username}" ({user.user_id}) logged out',
        )
