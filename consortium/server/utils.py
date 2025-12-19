import functools
import inspect
import uuid
from collections.abc import Callable


def normalize_uuid(value: str | uuid.UUID) -> str:
    return str(value)


def log_and_propagate_error_on_service_method(func) -> Callable:
    @functools.wraps(func)
    async def async_wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as exc:
            self._logger.error("{}", exc)
            raise

    @functools.wraps(func)
    def sync_wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as exc:
            self._logger.error("{}", exc)
            raise

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
