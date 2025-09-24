import abc
import asyncio
import enum
from typing import Any

from consortium.framework._life_cycles._life_cycle_status import (
    LifeCycleState,
    LifeCycleStatus,
)
from consortium.framework.exceptions._life_cycle_exceptions import (
    LifeCycleRuntimeError,
    LifeCycleStartError,
    LifeCycleStopError,
)
from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)
from consortium.server.exceptions.framework_exceptions.lifecycle_exceptions import (
    LifeCycleAlreadyStartedError,
    LifeCycleNotRunningError,
    LifeCycleRuntimeError as LifeCycleRuntimeFrameworkError,
    LifeCycleStartError as LifeCycleStartFrameworkError,
    LifeCycleStopError as LifeCycleStopFrameworkError,
)


# Provide additional context to the `on_fatal` handler denoting which part of the
# lifecycle the transition to fatal occurred from. Used primarily for logging.
class LifeCycleFatalContext(enum.StrEnum):
    START = enum.auto()
    RUNNING = enum.auto()
    STOP = enum.auto()
    CANCEL = enum.auto()
    ERROR = enum.auto()


# Life cycles are abstractions of entities that can run separately from the event loop.
# They handle starting, stopping, cancelling and manage state transitions based on
# signalling errors raised from hook methods.
class LifeCycle(abc.ABC):
    def __init__(self):
        self.status = LifeCycleStatus()
        self.stop_event = asyncio.Event()
        self._runtime_loop_task = None

    @abc.abstractmethod
    async def on_started(self) -> None: ...

    @abc.abstractmethod
    async def on_running(self) -> None: ...

    @abc.abstractmethod
    async def on_completed(self) -> None: ...

    @abc.abstractmethod
    async def on_stopped(self) -> None: ...

    @abc.abstractmethod
    async def on_cancelled(self) -> None: ...

    @abc.abstractmethod
    async def on_errored(self, runtime_error: BaseFrameworkException) -> None: ...

    @abc.abstractmethod
    async def on_fatal(
        self,
        exc: Exception,
        fatal_context: LifeCycleFatalContext,
    ) -> None: ...

    @abc.abstractmethod
    def to_json(self) -> dict[str, Any]: ...

    async def start(self) -> None:
        if (
            self.status.state
            not in (
                LifeCycleState.INITIALIZED,
                LifeCycleState.STOPPED,
                LifeCycleState.CANCELLED,
                LifeCycleState.ERRORED,
            )
            or self.status.state == LifeCycleState.FATAL
            and self._runtime_loop_task is not None
        ):
            raise LifeCycleAlreadyStartedError

        self.stop_event.clear()

        self.status._transition_to_started()

        try:
            await self.on_started()
        except LifeCycleStartError as exc:
            self.status._transition_to_initialized()
            raise LifeCycleStartFrameworkError(
                message=exc.message,
                detail=exc.detail,
            ) from None
        except Exception as exc:
            self.status._transition_to_fatal(exception=exc)
            await self.on_fatal(exc, fatal_context=LifeCycleFatalContext.START)
            raise exc

        self.stop_event.clear()
        self.status._transition_to_running()
        self._runtime_loop_task = asyncio.create_task(self._runtime_loop())

    async def stop(self) -> None:
        if self.status.state != LifeCycleState.RUNNING:
            raise LifeCycleNotRunningError

        try:
            await self.on_stopped()
        except LifeCycleStopError as exc:
            raise LifeCycleStopFrameworkError(
                message=exc.message,
                detail=exc.detail,
            ) from None
        except Exception as exc:
            self.status._transition_to_fatal(exception=exc)
            raise exc

        self.stop_event.set()

    async def cancel(self) -> None:
        if self.status.state != LifeCycleState.RUNNING:
            raise LifeCycleNotRunningError

        self._runtime_loop_task.cancel()

        try:
            await self._runtime_loop_task
            self.status._transition_to_cancelled()
        except asyncio.CancelledError:
            self.status._transition_to_cancelled()
        except Exception as exc:
            self.status._transition_to_fatal(exception=exc)
            raise exc
        finally:
            try:
                await self.on_cancelled()
            except Exception as exc:
                self.status._transition_to_fatal(exception=exc)
                await self.on_fatal(exc=exc, fatal_context=LifeCycleFatalContext.CANCEL)
                raise exc

    async def _runtime_loop(self) -> None:
        try:
            await self.on_running()
            self.status._transition_to_completed()
            await self.on_completed()
        except asyncio.CancelledError:
            return
        except LifeCycleRuntimeError as exc:
            self.status._transition_to_errored(
                error=LifeCycleRuntimeFrameworkError(
                    message=exc.message,
                    detail=exc.detail,
                ),
            )
            try:
                await self.on_errored(
                    runtime_error=LifeCycleRuntimeFrameworkError(
                        message=exc.message,
                        detail=exc.detail,
                    ),
                )
            except Exception as exc:
                self.status._transition_to_fatal(exception=exc)
                await self.on_fatal(exc=exc, fatal_context=LifeCycleFatalContext.ERROR)
        except Exception as exc:
            self.status._transition_to_fatal(exception=exc)
            await self.on_fatal(exc=exc, fatal_context=LifeCycleFatalContext.RUNNING)
