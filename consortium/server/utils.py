import functools
import inspect
import uuid
from collections.abc import Callable

from consortium.server.exceptions.consortium_exceptions.base_consortium_exception import (
    BaseConsortiumError,
)


def normalize_uuid(value: str | uuid.UUID) -> str:
    return str(value)


def log_and_propagate_error_on_service_method(func) -> Callable:
    @functools.wraps(func)
    async def async_wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except BaseConsortiumError as exc:
            self._logger.error("{}: {}", type(exc).__name__, exc)
            raise
        except Exception as exc:
            self._logger.opt(ansi=True, exception=exc).critical(
                "<white><RED><bold>Unhandled exception in {}.{}. {}: {}</></></>",
                type(self).__name__,
                func.__name__,
                type(exc).__name__,
                exc,
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except BaseConsortiumError as exc:
            self._logger.error("{}: {}", type(exc).__name__, exc)
            raise
        except Exception as exc:
            self._logger.opt(ansi=True, exception=exc).critical(
                "<white><RED><bold>Unhandled exception in {}.{}. {}: {}</></></>",
                type(self).__name__,
                func.__name__,
                type(exc).__name__,
                exc,
            )
            raise

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
