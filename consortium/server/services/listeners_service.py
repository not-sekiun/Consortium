from loguru import logger

from consortium.server.framework.base_listener import BaseListener


class ListenersService:
    def __init__(self):
        self._listeners = {}
        self.listeners_service_logger = logger.bind(
            logger_name=str(self),
        )
        self.listeners_service_logger.debug(
            f"Started {self}",
        )

    # Unlike user_accounts_service.py, we don't create the listener in this method
    # because we already have dedicated listener template objects that do that for us
    def add_listener(self, listener: BaseListener) -> None:
        if str(listener.listener_id) in self._listeners:
            raise ValueError(
                f"Cannot add listener to service because a listener with the same "
                f"listener ID already exists: {listener.listener_id}",
            )

        self._listeners[str(listener.listener_id)] = listener
        self.listeners_service_logger.debug(f"Added listener: {listener!r}")
        self.listeners_service_logger.info(f"Added listener: {listener}")

    def get_listener_by_listener_id(self, listener_id: str) -> BaseListener:
        try:
            listener = self._listeners[listener_id]
        except KeyError:
            raise ValueError(
                f"No listener exists with the provided listener ID: {listener_id}",
            )

        self.listeners_service_logger.debug(f"Retrieved listener: {listener!r}")
        return listener

    def get_all_listeners(self) -> list[BaseListener]:
        all_listeners = list(self._listeners.values())
        self.listeners_service_logger.debug(
            f"Retrieved all listeners ({len(all_listeners)} retrieved)",
        )
        return all_listeners

    def remove_listener(self, listener: BaseListener) -> None:
        try:
            del self._listeners[str(listener.listener_id)]
        except KeyError:
            raise ValueError(f"Listener does not exist: {listener}")

        self.listeners_service_logger.info(f"Removed listener: {listener}")
        self.listeners_service_logger.debug(f"Removed listener: {listener!r}")

    def __str__(self) -> str:
        return "Consortium Listeners Service"

    def __repr__(self) -> str:
        return "ListenersService()"
