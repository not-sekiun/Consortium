import abc
import asyncio
import enum

from consortium.framework._components._component_status import State, Status
from consortium.framework.exceptions._component_framework_exceptions import (
    ComponentRuntimeError,
    ComponentStartError,
    ComponentStopError,
)
from consortium.server.exceptions.consortium_exceptions.components_consortium_exceptions import (
    ComponentAlreadyRunningError,
    ComponentNotRunningError,
    ComponentRuntimeError as ComponentRuntimeFrameworkError,
    ComponentStartError as ComponentStartFrameworkError,
    ComponentStopError as ComponentStopFrameworkError,
)
from consortium.server.exceptions.framework_exceptions.base_framework_exception import (
    BaseFrameworkException,
)


# Provide additional context to the `on_fatal` handler denoting which part of the
# lifecycle the transition to fatal occurred from. Used primarily for logging.
class ComponentLifeCycleFatalContext(enum.StrEnum):
    START = enum.auto()
    RUNNING = enum.auto()
    STOP = enum.auto()
    CANCEL = enum.auto()
    ERROR = enum.auto()


# Life cycles are abstractions of entities that can run separately from the event loop.
# They handle starting, stopping, cancelling and manage state transitions based on
# signalling errors raised from hook methods.
class ComponentLifeCycle(abc.ABC):
    def __init__(self):
        self.status = Status()
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
    async def on_errored(self, error: BaseFrameworkException) -> None: ...

    @abc.abstractmethod
    async def on_fatal(
        self,
        exc: Exception,
        fatal_context: ComponentLifeCycleFatalContext,
    ) -> None: ...

    async def start(self) -> None:
        if (
            self.status.state
            not in (
                State.INITIALIZED,
                State.STOPPED,
                State.CANCELLED,
                State.ERRORED,
            )
            or self.status.state == State.FATAL
            and self._runtime_loop_task is not None
        ):
            raise ComponentAlreadyRunningError

        self.stop_event.clear()

        self.status._transition_to_started()

        try:
            await self.on_started()
        except ComponentStartError as exc:
            self.status._transition_to_initialized()
            raise ComponentStartFrameworkError(
                component_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            ) from None
        except Exception as exc:
            self.status._transition_to_fatal(
                error=self._construct_component_runtime_error_from_exception(exc=exc),
            )
            await self.on_fatal(exc, fatal_context=ComponentLifeCycleFatalContext.START)
            raise exc

        self.stop_event.clear()
        self.status._transition_to_running()
        self._runtime_loop_task = asyncio.create_task(self._runtime_loop())

    async def stop(self) -> None:
        if self.status.state != State.RUNNING:
            raise ComponentNotRunningError

        try:
            await self.on_stopped()
        except ComponentStopError as exc:
            raise ComponentStopFrameworkError(
                component_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            ) from None
        except Exception as exc:
            self.status._transition_to_fatal(
                error=self._construct_component_runtime_error_from_exception(exc=exc),
            )
            raise exc

        self.stop_event.set()

    async def cancel(self) -> None:
        if self.status.state != State.RUNNING:
            raise ComponentNotRunningError

        self._runtime_loop_task.cancel()

        try:
            await self._runtime_loop_task
            self.status._transition_to_cancelled()
        except asyncio.CancelledError:
            self.status._transition_to_cancelled()
        except Exception as exc:
            self.status._transition_to_fatal(
                error=self._construct_component_runtime_error_from_exception(exc=exc),
            )
            raise exc
        finally:
            try:
                await self.on_cancelled()
            except Exception as exc:
                self.status._transition_to_fatal(
                    error=self._construct_component_runtime_error_from_exception(
                        exc=exc,
                    ),
                )
                await self.on_fatal(
                    exc=exc,
                    fatal_context=ComponentLifeCycleFatalContext.CANCEL,
                )
                raise exc

    def _construct_component_runtime_error_from_exception(
        self,
        exc,
    ) -> ComponentRuntimeFrameworkError:
        return ComponentRuntimeFrameworkError(
            component_str=str(self),
            error_message=f"{type(exc).__name__}: {exc}",
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

    async def _runtime_loop(self) -> None:
        try:
            await self.on_running()
            self.status._transition_to_completed()
            await self.on_completed()
        except asyncio.CancelledError:
            return
        except ComponentRuntimeError as exc:
            self.status._transition_to_errored(
                error=ComponentRuntimeFrameworkError(
                    error_message=exc.message,
                    detail=exc.detail,
                ),
            )
            try:
                await self.on_errored(
                    error=ComponentRuntimeFrameworkError(
                        component_str=str(self),
                        error_message=exc.message,
                        detail=exc.detail,
                    ),
                )
            except Exception as exc:
                self.status._transition_to_fatal(
                    error=self._construct_component_runtime_error_from_exception(
                        exc=exc,
                    ),
                )
                await self.on_fatal(
                    exc=exc,
                    fatal_context=ComponentLifeCycleFatalContext.ERROR,
                )
        except Exception as exc:
            self.status._transition_to_fatal(
                error=self._construct_component_runtime_error_from_exception(exc=exc),
            )
            await self.on_fatal(
                exc=exc,
                fatal_context=ComponentLifeCycleFatalContext.RUNNING,
            )
