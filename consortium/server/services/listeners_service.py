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
        self._listeners[str(listener.listener_id)] = listener
        self._listeners_service_logger.info(
            f'Listener "{listener.name}" ({listener.listener_id}) was created',
        )

    def get_listener_by_listener_id(self, listener_id: str) -> BaseListener:
        return self._listeners[listener_id]

    def get_all_listeners(self) -> list[BaseListener]:
        return list(self._listeners.values())

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
