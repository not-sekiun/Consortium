from loguru import logger

from consortium.server.framework.base_listener import BaseListener


class ListenersService:
    def __init__(self):
        self._listeners = {}
        self._listeners_service_logger = logger.bind(
            logger_name="Consortium Listeners Service",
        )

    # Unlike user_accounts_service.py, we don't create the listener in this method
    # because we already have dedicated listener template objects that do that for us
    def add_listener(self, listener: BaseListener) -> None:
        if str(listener.listener_id) in self._listeners:
            raise ValueError(
                f'Listener "{listener.name}" ({listener.listener_id}) already exists',
            )

        self._listeners[str(listener.listener_id)] = listener
        self._listeners_service_logger.info(
            f'Listener "{listener.name}" ({listener.listener_id}) was created',
        )

    def get_listener_by_listener_id(self, listener_id: str) -> BaseListener:
        try:
            listener = self._listeners[listener_id]
        except KeyError:
            raise ValueError(
                f'Listener with the listener ID "{listener_id}" does not exist',
            )

        self._listeners_service_logger.debug(
            f'Retrieved listener "{listener.name}" ({listener_id})',
        )
        return listener

    def get_all_listeners(self) -> list[BaseListener]:
        all_listeners = list(self._listeners.values())
        self._listeners_service_logger.debug(
            f"Retrieved all listeners ({len(all_listeners)} retrieved)",
        )
        return all_listeners

    def remove_listener(self, listener: BaseListener) -> None:
        try:
            del self._listeners[str(listener.listener_id)]
        except KeyError:
            raise ValueError(
                f'Listener "{listener.name}" ({listener.listener_id}) does not exist',
            )

        self._listeners_service_logger.info(
            f'Listener "{listener.name}" ({listener.listener_id}) was removed',
        )
