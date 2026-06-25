import abc
import asyncio
import enum

from consortium.framework._components._component_status import State, Status
from consortium.framework.exceptions import (
    _component_framework_exceptions as framework_excs,
)
from consortium.server.exceptions.consortium_exceptions import (
    components_consortium_exceptions as consortium_excs,
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
# They handle starting, stopping, cancelling and manage status transitions based on
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
    async def on_errored(
        self, error: consortium_excs.ComponentRuntimeError
    ) -> None: ...

    @abc.abstractmethod
    async def on_fatal(
        self,
        exc: Exception,
        fatal_context: ComponentLifeCycleFatalContext,
    ) -> None: ...

    async def start(self) -> None:
        if self.status.state in (State.RUNNING, State.STARTED):
            raise consortium_excs.ComponentAlreadyRunningError(
                component_str=str(self),
            )

        self.stop_event.clear()

        self.status._transition_to_started()

        try:
            await self.on_started()
        except framework_excs.ComponentStartError as exc:
            self.status._transition_to_initialized()
            raise consortium_excs.ComponentStartError(
                component_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            ) from None
        except Exception as exc:
            self.status._transition_to_fatal(
                error=self._construct_component_runtime_error_from_unhandled_exception(
                    exc=exc
                ),
            )
            await self.on_fatal(exc, fatal_context=ComponentLifeCycleFatalContext.START)
            raise exc

        self.stop_event.clear()

        self._runtime_loop_task = asyncio.create_task(self._runtime_loop())
        self._runtime_loop_task.add_done_callback(self._clear_runtime_loop_task)

    async def stop(self) -> None:
        if self.status.state != State.RUNNING:
            raise consortium_excs.ComponentNotRunningError(
                component_str=str(self),
            )

        try:
            self.status._transition_to_stopping()
            await self.on_stopped()
            self.status._transition_to_stopped()
        except framework_excs.ComponentStopError as exc:
            raise consortium_excs.ComponentStopError(
                component_str=str(self),
                error_message=exc.message,
                detail=exc.detail,
            ) from None
        except Exception as exc:
            self.status._transition_to_fatal(
                error=self._construct_component_runtime_error_from_unhandled_exception(
                    exc=exc
                ),
            )
            raise exc

        self.stop_event.set()

    async def cancel(self) -> None:
        if self.status.state != State.RUNNING:
            raise consortium_excs.ComponentNotRunningError(
                component_str=str(self),
            )

        self._runtime_loop_task.cancel()

        _actually_cancelled = False
        try:
            await self._runtime_loop_task
            # The task completed naturally before the cancellation could interrupt
            # it (race between the RUNNING check and the task finishing). Accept
            # whatever terminal state the task already transitioned to.
        except asyncio.CancelledError:
            _actually_cancelled = True
            self.status._transition_to_cancelled()
        except Exception as exc:
            self.status._transition_to_fatal(
                error=self._construct_component_runtime_error_from_unhandled_exception(
                    exc=exc
                ),
            )
            raise exc

        if _actually_cancelled:
            try:
                await self.on_cancelled()
            except Exception as exc:
                self.status._transition_to_fatal(
                    error=self._construct_component_runtime_error_from_unhandled_exception(
                        exc=exc,
                    ),
                )
                await self.on_fatal(
                    exc=exc,
                    fatal_context=ComponentLifeCycleFatalContext.CANCEL,
                )
                raise exc

    async def wait_until_started(self) -> None:
        while self.status.state in (State.INITIALIZED, State.STARTED):
            await asyncio.sleep(0)

    async def wait_until_stopped(self) -> None:
        if self._runtime_loop_task is not None:
            try:
                await self._runtime_loop_task
            except asyncio.CancelledError:
                pass

    def reset(self) -> None:
        self.status._transition_to_initialized()
        self.stop_event.clear()
        self._runtime_loop_task = None

    def _construct_component_runtime_error_from_framework_runtime_error(
        self,
        error: framework_excs.ComponentRuntimeError,
    ) -> consortium_excs.ComponentRuntimeError:
        return consortium_excs.ComponentRuntimeError(
            component_str=str(self),
            error_message=error.message,
            detail=error.detail,
        )

    def _construct_component_runtime_error_from_unhandled_exception(
        self,
        exc: Exception,
    ) -> consortium_excs.ComponentRuntimeError:
        return consortium_excs.ComponentRuntimeError(
            component_str=str(self),
            error_message=(
                f"An unhandled exception was raised while running. "
                f"{type(exc).__name__}: {exc}"
            ),
            detail={
                "type": type(exc).__name__,
                "message": str(exc),
            },
        )

    async def _runtime_loop(self) -> None:
        try:
            self.status._transition_to_running()
            await self.on_running()

            if self.stop_event.is_set():
                # `stop()` was called during `on_running()` so we should skip the
                # completed state transition and hook method because we did not run all
                # the way to completion
                return

            self.status._transition_to_completed()
            await self.on_completed()
        except asyncio.CancelledError:
            return
        except framework_excs.ComponentRuntimeError as exc:
            component_runtime_error = (
                self._construct_component_runtime_error_from_framework_runtime_error(
                    error=exc,
                )
            )
            self.status._transition_to_errored(error=component_runtime_error)
            try:
                await self.on_errored(error=component_runtime_error)
            except Exception as exc:
                self.status._transition_to_fatal(
                    error=self._construct_component_runtime_error_from_unhandled_exception(
                        exc=exc,
                    ),
                )
                await self.on_fatal(
                    exc=exc,
                    fatal_context=ComponentLifeCycleFatalContext.ERROR,
                )
        except Exception as exc:
            self.status._transition_to_fatal(
                error=self._construct_component_runtime_error_from_unhandled_exception(
                    exc=exc
                ),
            )
            await self.on_fatal(
                exc=exc,
                fatal_context=ComponentLifeCycleFatalContext.RUNNING,
            )

    def _clear_runtime_loop_task(self, _task: asyncio.Task) -> None:
        self._runtime_loop_task = None
