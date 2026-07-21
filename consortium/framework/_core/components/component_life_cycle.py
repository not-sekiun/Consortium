import abc
import asyncio
import enum

from consortium.framework._core.components.component_status import State, Status
from consortium.framework._core.framework_exceptions import (
    components_framework_exceptions as frmwrk_excs,
)
from consortium.framework.signal_exceptions import (
    _component_signal_exceptions as sig_excs,
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
        # Serializes start()/stop()/cancel() so overlapping calls cannot both pass
        # their precondition guard: the precondition is re-checked under the lock so
        # exactly one wins and the loser gets a clean framework error.
        self._lifecycle_lock = asyncio.Lock()
        # Set once a start attempt has concluded, whether it reached RUNNING or failed
        # and rolled back. wait_until_started() blocks on this so a failed start cannot
        # leave a waiter spinning on the ambiguous INITIALIZED state.
        self._start_concluded = asyncio.Event()

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
    async def on_errored(self, error: frmwrk_excs.ComponentRuntimeError) -> None: ...

    @abc.abstractmethod
    async def on_fatal(
        self,
        exc: Exception,
        fatal_context: ComponentLifeCycleFatalContext,
    ) -> None: ...

    async def start(self) -> None:
        async with self._lifecycle_lock:
            if self.status.state in (State.RUNNING, State.STARTED):
                raise frmwrk_excs.ComponentAlreadyRunningError(
                    component_str=str(self),
                )

            self.stop_event.clear()
            # A fresh start attempt is now pending. It concludes either when the runtime
            # loop reaches RUNNING or when this method fails and rolls back below.
            self._start_concluded.clear()

            self.status._transition_to_started()

            try:
                await self.on_started()
            except sig_excs.ComponentStartError as exc:
                self.status._transition_to_initialized()
                self._start_concluded.set()
                raise frmwrk_excs.ComponentStartError(
                    component_str=str(self),
                    error_message=exc.message,
                    detail=exc.detail,
                ) from None
            except Exception as exc:
                self._start_concluded.set()
                await self._transition_to_fatal_and_notify(
                    exc=exc,
                    fatal_context=ComponentLifeCycleFatalContext.START,
                )
                raise exc

            self._runtime_loop_task = asyncio.create_task(self._runtime_loop())
            self._runtime_loop_task.add_done_callback(self._clear_runtime_loop_task)

    async def stop(self) -> None:
        async with self._lifecycle_lock:
            if self.status.state != State.RUNNING:
                raise frmwrk_excs.ComponentNotRunningError(
                    component_str=str(self),
                )

            self.status._transition_to_stopping()
            # Move to STOPPING before signalling: the state is what tells the runtime
            # loop a stop is in progress (so it skips the completion branch), while
            # stop_event exists only to wake an on_running() that is blocked waiting on
            # it. Setting it up front releases that body even on the fatal path below.
            self.stop_event.set()

            try:
                await self.on_stopped()
            except sig_excs.ComponentStopError as exc:
                # A refused stop rolls back to RUNNING and leaves the component live so
                # it can be stopped again later. `on_stopped()` raises the signal
                # synchronously, so the loop never observes the brief `stop_event` set.
                self.status._transition_to_running()
                self.stop_event.clear()
                raise frmwrk_excs.ComponentStopError(
                    component_str=str(self),
                    error_message=exc.message,
                    detail=exc.detail,
                ) from None
            except Exception as exc:
                await self._transition_to_fatal_and_notify(
                    exc=exc,
                    fatal_context=ComponentLifeCycleFatalContext.STOP,
                )
                raise exc

            self.status._transition_to_stopped()

    async def cancel(self) -> None:
        async with self._lifecycle_lock:
            if self.status.state != State.RUNNING:
                raise frmwrk_excs.ComponentNotRunningError(
                    component_str=str(self),
                )

            task = self._runtime_loop_task

            # State is RUNNING under the lock, so the runtime loop has not finished and
            # its task is live (the loop always transitions away from RUNNING before its
            # task completes). Guard against a missing task defensively all the same.
            if task is None or task.done():
                self.status._transition_to_cancelled()
                return

            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            # The task may have reached its own terminal state before the cancellation
            # landed (a natural completion racing the cancel). Accept whatever terminal
            # state it settled on and skip the hook.
            if self.status.state is not State.RUNNING:
                return

            self.status._transition_to_cancelled()

            try:
                await self.on_cancelled()
            except Exception as exc:
                await self._transition_to_fatal_and_notify(
                    exc=exc,
                    fatal_context=ComponentLifeCycleFatalContext.CANCEL,
                )
                raise exc

    async def wait_until_started(self) -> None:
        # RUNNING or any state past it (STOPPING, terminal) means there is nothing left
        # to wait on. INITIALIZED and STARTED are the only pending-start states.
        if self.status.state not in (State.INITIALIZED, State.STARTED):
            return
        # A start is pending or in progress. Block until it concludes rather than
        # polling on state identity, since a failed start rolls back to the same
        # INITIALIZED state it started from.
        await self._start_concluded.wait()

    async def wait_until_stopped(self) -> None:
        task = self._runtime_loop_task
        # No live task means the component either never started or has already come to
        # rest (the done callback nulls the handle on completion). Either way there is
        # nothing to join on.
        if task is None:
            return
        try:
            # Shield so a cancellation aimed at the caller of this coroutine does not
            # cascade into the runtime task: `await task` would otherwise cancel the
            # very task we are joining on.
            await asyncio.shield(task)
        except asyncio.CancelledError:
            # Absorb only the runtime task's own cancellation. If the task itself is not
            # cancelled the CancelledError targets the caller and must propagate.
            if task.cancelled():
                return
            raise

    def reset(self) -> None:
        # reset() is legal only from INITIALIZED or a terminal state. A live component
        # must be stopped or cancelled first; resetting it here would orphan the runtime
        # loop task, which would then transition the freshly reset status back to
        # RUNNING.
        if self.status.state in (State.STARTED, State.RUNNING, State.STOPPING):
            raise frmwrk_excs.ComponentAlreadyRunningError(
                component_str=str(self),
            )
        self.status._transition_to_initialized()
        self.stop_event.clear()
        self._runtime_loop_task = None

    def _construct_component_runtime_error_from_framework_runtime_error(
        self,
        error: sig_excs.ComponentRuntimeError,
    ) -> frmwrk_excs.ComponentRuntimeError:
        return frmwrk_excs.ComponentRuntimeError(
            component_str=str(self),
            error_message=error.message,
            detail=error.detail,
        )

    def _construct_component_runtime_error_from_unhandled_exception(
        self,
        exc: Exception,
    ) -> frmwrk_excs.ComponentRuntimeError:
        return frmwrk_excs.ComponentRuntimeError(
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

    async def _transition_to_fatal_and_notify(
        self,
        exc: Exception,
        fatal_context: ComponentLifeCycleFatalContext,
    ) -> None:
        self.status._transition_to_fatal(
            error=self._construct_component_runtime_error_from_unhandled_exception(
                exc=exc,
            ),
        )
        await self._invoke_fatal_hook(exc=exc, fatal_context=fatal_context)

    async def _invoke_fatal_hook(
        self,
        exc: Exception,
        fatal_context: ComponentLifeCycleFatalContext,
    ) -> None:
        # on_fatal() is the last resort handler. If it raises, the failure must never
        # propagate (in the runtime loop task nobody would retrieve it) and must never
        # recurse back into on_fatal(). The component stays FATAL carrying the original
        # error, with the secondary failure chained onto it so it is not lost.
        try:
            await self.on_fatal(exc=exc, fatal_context=fatal_context)
        except Exception as handler_exc:
            # Chain the secondary failure onto the stored error. The original error
            # remains the primary cause of the FATAL state; the handler failure hangs
            # off it as its __cause__.
            # TODO: surface this chained handler error through Status.to_json() once the
            # shape for exposing chained exceptions is decided.
            if isinstance(self.status.error, frmwrk_excs.ComponentRuntimeError):
                self.status.error.__cause__ = handler_exc

    async def _runtime_loop(self) -> None:
        try:
            self.status._transition_to_running()
            # A start attempt has now reached RUNNING; release any wait_until_started().
            self._start_concluded.set()
            await self.on_running()

            # The lifecycle state, not stop_event, decides whether this was a
            # completion. stop_event is purely a signalling primitive that stop() uses
            # to wake a blocked on_running(); a component never sets it itself. If a stop
            # (or any other terminal transition) is in progress the state has already
            # advanced past RUNNING, so the completion path is skipped. If the state is
            # still RUNNING then on_running() returning is a genuine completion.
            if self.status.state is State.RUNNING:
                self.status._transition_to_completed()
                await self.on_completed()
        except asyncio.CancelledError:
            # Re-raise so the task is genuinely cancelled (task.cancelled() is True and
            # awaiting it raises), which is what cancel() relies on to reach CANCELLED.
            raise
        except sig_excs.ComponentRuntimeError as signal_exc:
            component_runtime_error = (
                self._construct_component_runtime_error_from_framework_runtime_error(
                    error=signal_exc,
                )
            )
            self.status._transition_to_errored(error=component_runtime_error)
            try:
                await self.on_errored(error=component_runtime_error)
            except asyncio.CancelledError:
                raise
            except Exception as hook_exc:
                await self._transition_to_fatal_and_notify(
                    exc=hook_exc,
                    fatal_context=ComponentLifeCycleFatalContext.ERROR,
                )
        except Exception as unhandled_exc:
            await self._transition_to_fatal_and_notify(
                exc=unhandled_exc,
                fatal_context=ComponentLifeCycleFatalContext.RUNNING,
            )

    def _clear_runtime_loop_task(self, _task: asyncio.Task) -> None:
        self._runtime_loop_task = None
