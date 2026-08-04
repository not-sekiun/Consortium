import uuid

from loguru import logger

import consortium.server.server_singletons as server_singletons
from consortium.framework.event_hooks.event_type import EventType
from consortium.server.exceptions.service_exceptions.users_service_exceptions import (
    UserAccessTokenNotFoundError,
    UserIDNotFoundError,
)
from consortium.server.models.logging_models import LoggerType
from consortium.server.objects.user_objects import User
from consortium.server.services.events_service import EventsService
from consortium.server.utils import (
    log_and_propagate_error_on_service_method,
    normalize_uuid,
    run_async_background_task,
)


class UsersService:
    def __init__(self, events_service: EventsService) -> None:
        self._events_service = events_service
        self._users = {}
        self._logger = logger.bind(
            logger_name=str(self), logger_type=LoggerType.SERVICE_LOGGER
        )
        self._logger.debug("Started {}", self)

    def __str__(self) -> str:
        return "Users Service"

    def __repr__(self) -> str:
        return "UsersService()"

    @log_and_propagate_error_on_service_method
    def get_user_by_user_id(self, user_id: str | uuid.UUID) -> User:
        """Returns a currently logged-in user by their user ID.

        Args:
            user_id: The ID of the user to retrieve.

        Returns:
            The user with the specified ID.

        Raises:
            UserIDNotFoundError: If no logged-in user with the given ID exists.
        """
        user_id = normalize_uuid(user_id)

        try:
            user = self._users[user_id]
        except KeyError:
            raise UserIDNotFoundError(user_id=user_id) from None

        self._logger.debug("Retrieved user by user ID '{}': {!r}", user_id, user)
        return user

    @log_and_propagate_error_on_service_method
    def get_user_by_access_token(self, access_token: str) -> User:
        """Returns a currently logged-in user by their access token.

        Args:
            access_token: The JWT subject string used as the access token.

        Returns:
            The user whose access token matches.

        Raises:
            UserAccessTokenNotFoundError: If no logged-in user has the given access
                token.
        """
        for user in self.get_all_users():
            if str(user.json_web_token.subject) == access_token:
                self._logger.debug(
                    "Retrieved user by access value '{}': {!r}", access_token, user
                )
                return user
        raise UserAccessTokenNotFoundError(access_token=access_token)

    @log_and_propagate_error_on_service_method
    def get_all_users(self) -> list[User]:
        """Returns all currently logged-in users.

        Returns:
            A list of all active user sessions. Empty if no users are logged in.
        """
        all_users = list(self._users.values())
        self._logger.debug(
            "Retrieved all users ({} user(s) retrieved)",
            len(all_users),
        )
        return all_users

    @log_and_propagate_error_on_service_method
    def update_user_display_name_by_user_id(
        self,
        display_name: str,
        user_id: str | uuid.UUID,
    ) -> User:
        """Updates the display name of a logged-in user.

        Args:
            display_name: The new display name to set.
            user_id: The ID of the user to update.

        Returns:
            The updated user.

        Raises:
            UserIDNotFoundError: If no logged-in user with the given ID exists.
        """
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

    @log_and_propagate_error_on_service_method
    def login_user(self, username: str, password: str) -> User:
        """Authenticates a user account and creates an active user session.

        Emits a `USER_LOGGED_IN` event after successful login.

        Args:
            username: The username of the account to authenticate.
            password: The password of the account to authenticate.

        Returns:
            The newly created user session.

        Raises:
            UserAccountAuthenticationError: If no account with the given username
                exists, or if the password does not match.
            RuntimeError: If called with no running event loop. The `USER_LOGGED_IN`
                event is scheduled with `asyncio.create_task`, which requires one.
        """
        user_account = server_singletons.user_accounts_service.authenticate_user_account_credentials(
            username=username,
            password=password,
        )
        user = User(user_account=user_account)
        self._users[str(user.user_id)] = user

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.USER_LOGGED_IN,
                message=f"User logged in: {user}",
                data=user.to_json(),
            )
        )
        self._logger.info("User logged in: {}", user)
        self._logger.debug("- {!r}", user)

        return user

    @log_and_propagate_error_on_service_method
    def logout_user_by_user_id(self, user_id: str | uuid.UUID) -> None:
        """Ends a user session and removes it from the active users registry.

        Emits a `USER_LOGGED_OUT` event after successful logout.

        Args:
            user_id: The ID of the user session to end.

        Raises:
            UserIDNotFoundError: If no logged-in user with the given ID exists.
            RuntimeError: If called with no running event loop. The `USER_LOGGED_OUT`
                event is scheduled with `asyncio.create_task`, which requires one.
        """
        user = self.get_user_by_user_id(user_id=user_id)

        deleted_user = self._users.pop(str(user.user_id))

        run_async_background_task(
            coroutine=self._events_service.trigger_event(
                event_type=EventType.USER_LOGGED_OUT,
                message=f"User logged out: {deleted_user}",
                data={"user_id": str(user.user_id)},
            )
        )
        self._logger.info("User logged out: {}", deleted_user)
        self._logger.debug("- {!r}", deleted_user)
