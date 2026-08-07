import asyncio
import inspect
from collections.abc import Callable

import pytest
from packaging import requirements, specifiers, version

from consortium.framework._core.components import (
    ComponentLifeCycle,
    ComponentLifeCycleExceptions,
    ComponentLifeCyclePhase,
    ComponentMetadata,
    State,
)
from consortium.framework._core.components.component_life_cycle import (
    _PHASE_TO_OPERATION_MAP,
)
from consortium.framework._core.components.component_status import Status
from consortium.framework._core.framework_exceptions import (
    components_framework_exceptions as frmwrk_excs,
)
from consortium.framework.signal_exceptions import (
    _component_signal_exceptions as sig_excs,
)

pytestmark = pytest.mark.anyio

# Upper bound for any await that is expected to complete promptly. Kept small so that a
# contract violation surfaces as a fast failure instead of a hung test session.
_TIMEOUT = 0.5

# Every state that is not RUNNING, used to prove the `stop()`/`cancel()` guards.
_NON_RUNNING_STATES = [state for state in State if state is not State.RUNNING]

# States a component can come to rest in once its runtime loop has finished.
_TERMINAL_STATES = [
    State.COMPLETED,
    State.STOPPED,
    State.CANCELLED,
    State.ERRORED,
    State.FATAL,
]

# States that must carry an error on the status object.
_ERROR_STATES = (State.ERRORED, State.FATAL)

_LEGAL_EDGES = [
    (source, destination)
    for source, destinations in Status._valid_state_transitions.items()
    for destination in destinations
]

_ILLEGAL_EDGES = [
    (source, destination)
    for source in State
    for destination in State
    if destination not in Status._valid_state_transitions[source]
]


def _runtime_error(message: str = "runtime error") -> frmwrk_excs.ComponentRuntimeError:
    return frmwrk_excs.ComponentRuntimeError(
        component_str="test-component",
        error_message=message,
        detail={},
    )


def _fatal_error(
    underlying_exception: Exception | None = None,
    operation: str = "start",
    phase: ComponentLifeCyclePhase = ComponentLifeCyclePhase.START,
) -> frmwrk_excs.ComponentFatalError:
    return frmwrk_excs.ComponentFatalError(
        component_str="test-component",
        operation=operation,
        phase=str(phase),
        underlying_exception=underlying_exception or ValueError("fatal error"),
    )


# The error type a status carries in each of its two error states. FATAL carries a
# ComponentFatalError and ERRORED a ComponentRuntimeError, so a helper that stands in for
# "whatever error this state requires" has to pick by state.
def _error_for_state(state: State) -> frmwrk_excs.ComponentOperationError | None:
    if state is State.FATAL:
        return _fatal_error()
    if state is State.ERRORED:
        return _runtime_error()
    return None


# Build a zero argument callable that raises `exc`, for use as a hook behaviour.
def _raises(exc: BaseException) -> Callable[[], None]:
    def _behaviour() -> None:
        raise exc

    return _behaviour


# Yield control to the event loop enough times for a pending runtime loop task to make
# progress. Used where the contract deliberately does not synchronise.
async def _settle(iterations: int = 10) -> None:
    for _ in range(iterations):
        await asyncio.sleep(0)


# A concrete life cycle whose every hook records that it ran and then executes an
# optional per test behaviour. Behaviours are plain callables; if one returns an
# awaitable it is awaited, so `component.stop_event.wait` can be installed directly to
# model a long running component.
class _RecordingComponent(ComponentLifeCycle):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []
        self.behaviours: dict[str, Callable[[], object]] = {}
        self.errored_with: list[frmwrk_excs.ComponentRuntimeError] = []
        self.fatal_calls: list[tuple[BaseException, ComponentLifeCyclePhase]] = []

    def __str__(self) -> str:
        return "test-component"

    async def _dispatch(self, hook: str) -> None:
        self.calls.append(hook)
        behaviour = self.behaviours.get(hook)
        if behaviour is None:
            return
        result = behaviour()
        if inspect.isawaitable(result):
            await result

    async def on_started(self) -> None:
        await self._dispatch("on_started")

    async def on_running(self) -> None:
        await self._dispatch("on_running")

    async def on_completed(self) -> None:
        await self._dispatch("on_completed")

    async def on_stopped(self) -> None:
        await self._dispatch("on_stopped")

    async def on_cancelled(self) -> None:
        await self._dispatch("on_cancelled")

    async def on_errored(self, error: frmwrk_excs.ComponentRuntimeError) -> None:
        self.errored_with.append(error)
        await self._dispatch("on_errored")

    async def on_fatal(
        self,
        exc: Exception,
        phase: ComponentLifeCyclePhase,
    ) -> None:
        self.fatal_calls.append((exc, phase))
        await self._dispatch("on_fatal")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def component() -> _RecordingComponent:
    return _RecordingComponent()


# A component whose `on_running()` blocks until a stop is requested, i.e. the long
# running shape of a component rather than the finite unit of work shape.
@pytest.fixture
def blocking_component() -> _RecordingComponent:
    instance = _RecordingComponent()
    instance.behaviours["on_running"] = instance.stop_event.wait
    return instance


async def _bring_to_running(instance: _RecordingComponent) -> None:
    await instance.start()
    await asyncio.wait_for(instance.wait_until_started(), timeout=_TIMEOUT)
    assert instance.status.state is State.RUNNING


# Force a status onto a component without going through the life cycle. Used only by the
# precondition guard tests, which must be independent of whether the paths that normally
# produce those states are themselves working.
def _force_state(instance: _RecordingComponent, state: State) -> None:
    instance.status.state = state
    instance.status.error = _error_for_state(state)


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


def test_status_starts_initialized_with_no_error():
    status = Status()

    assert status.state is State.INITIALIZED
    assert status.error is None


@pytest.mark.parametrize(("source", "destination"), _LEGAL_EDGES)
def test_status_allows_every_legal_transition(source: State, destination: State):
    status = Status()
    status.state = source
    error = _error_for_state(destination)

    status._transition_to_state(new_state=destination, error=error)

    assert status.state is destination
    assert status.error is error


@pytest.mark.parametrize(("source", "destination"), _ILLEGAL_EDGES)
def test_status_rejects_every_illegal_transition(source: State, destination: State):
    status = Status()
    status.state = source
    error = _error_for_state(destination)

    with pytest.raises(AssertionError):
        status._transition_to_state(new_state=destination, error=error)


@pytest.mark.parametrize("destination", _ERROR_STATES)
def test_status_requires_an_error_for_error_states(destination: State):
    status = Status()
    status.state = State.RUNNING

    with pytest.raises(AssertionError):
        status._transition_to_state(new_state=destination)


@pytest.mark.parametrize(
    "destination",
    [state for state in State if state not in _ERROR_STATES],
)
def test_status_forbids_an_error_for_non_error_states(destination: State):
    status = Status()
    # RUNNING is the state with the widest set of outgoing edges, but it cannot reach
    # STARTED/RUNNING/INITIALIZED so pick a source that can reach the destination.
    status.state = next(
        source
        for source, destinations in Status._valid_state_transitions.items()
        if destination in destinations
    )

    with pytest.raises(AssertionError):
        status._transition_to_state(new_state=destination, error=_runtime_error())


def test_status_transition_helpers_reach_their_states(component: _RecordingComponent):
    status = component.status
    error = _runtime_error()

    status._transition_to_started()
    assert status.state is State.STARTED
    status._transition_to_running()
    assert status.state is State.RUNNING
    status._transition_to_stopping()
    assert status.state is State.STOPPING
    status._transition_to_stopped()
    assert status.state is State.STOPPED
    status._transition_to_initialized()
    assert status.state is State.INITIALIZED

    status._transition_to_started()
    status._transition_to_running()
    status._transition_to_completed()
    assert status.state is State.COMPLETED
    status._transition_to_started()
    status._transition_to_running()
    status._transition_to_cancelled()
    assert status.state is State.CANCELLED

    status._transition_to_started()
    status._transition_to_running()
    status._transition_to_errored(error=error)
    assert status.state is State.ERRORED
    assert status.error is error

    fatal_error = _fatal_error()
    status._transition_to_fatal(error=fatal_error)
    assert status.state is State.FATAL
    assert status.error is fatal_error


def test_status_str_and_repr_without_an_error():
    status = Status()

    assert str(status) == State.INITIALIZED
    assert repr(status) == f"Status(state={State.INITIALIZED!r}, error=None)"


def test_status_str_includes_the_error_when_present():
    status = Status()
    status.state = State.RUNNING
    error = _fatal_error(underlying_exception=ValueError("it broke"))
    status._transition_to_fatal(error=error)

    assert str(status) == f"{State.FATAL}: {error}"
    assert repr(status) == f"Status(state={State.FATAL!r}, error={error!r})"


def test_status_to_json_without_an_error():
    assert Status().to_json() == {"state": str(State.INITIALIZED), "error": None}


def test_status_to_json_with_a_component_runtime_error():
    status = Status()
    status.state = State.RUNNING
    error = _runtime_error(message="it broke")
    status._transition_to_errored(error=error)

    assert status.to_json() == {
        "state": str(State.ERRORED),
        "error": {
            "code": error.code,
            "message": error.message,
            "detail": error.detail,
        },
    }


# REGRESSION: to_json() used to gate serialization on ComponentRuntimeError alone. A
# ComponentFatalError is a sibling of that class, not a subclass, so a FATAL component
# would have serialized as an error-less failure and clients would have been told a
# component had died without being told why.
def test_status_to_json_with_a_component_fatal_error():
    status = Status()
    status.state = State.RUNNING
    error = _fatal_error(underlying_exception=ValueError("it broke"))
    status._transition_to_fatal(error=error)

    assert status.to_json() == {
        "state": str(State.FATAL),
        "error": {
            "code": error.code,
            "message": error.message,
            "detail": {
                "type": "ValueError",
                "message": "it broke",
                "phase": str(ComponentLifeCyclePhase.START),
            },
        },
    }


def test_status_to_json_ignores_a_foreign_error_object():
    status = Status()
    status.error = ValueError("not a component runtime error")

    assert status.to_json()["error"] is None


# ---------------------------------------------------------------------------
# ComponentFatalError
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("phase", "expected_operation"),
    [
        (ComponentLifeCyclePhase.START, "start"),
        (ComponentLifeCyclePhase.RUNNING, "run"),
        (ComponentLifeCyclePhase.STOP, "stop"),
        (ComponentLifeCyclePhase.CANCEL, "cancel"),
        (ComponentLifeCyclePhase.ERROR, "handle a runtime error within"),
    ],
)
def test_fatal_error_renders_the_operation_for_every_phase(
    phase: ComponentLifeCyclePhase,
    expected_operation: str,
):
    error = _fatal_error(
        underlying_exception=ValueError("boom"),
        operation=_PHASE_TO_OPERATION_MAP[phase],
        phase=phase,
    )

    assert error.message == (
        f"Failed to {expected_operation} the component test-component. An unhandled "
        f"exception was raised. ValueError: boom"
    )
    assert error.detail["phase"] == str(phase)


# An exception carrying no message renders as its bare type. Formatting it the usual way
# would leave a dangling "ValueError: " that reads as truncated output.
def test_fatal_error_omits_the_colon_for_an_empty_underlying_message():
    error = _fatal_error(underlying_exception=ValueError())

    assert error.message == (
        "Failed to start the component test-component. An unhandled exception was "
        "raised. ValueError"
    )
    assert error.detail == {
        "type": "ValueError",
        "message": "",
        "phase": str(ComponentLifeCyclePhase.START),
    }


# CONTRACT: `detail` crosses the API boundary through Status.to_json(), so it carries only
# what a client can act on. The traceback lives on __cause__, which does not.
def test_fatal_error_detail_carries_no_traceback():
    error = _fatal_error(underlying_exception=ValueError("boom"))

    assert set(error.detail) == {"type", "message", "phase"}


def test_fatal_error_starts_with_no_fatal_hook_error():
    assert _fatal_error().fatal_hook_error is None


# ---------------------------------------------------------------------------
# start()
# ---------------------------------------------------------------------------


async def test_start_transitions_to_started_then_running(
    blocking_component: _RecordingComponent,
):
    await blocking_component.start()

    # CONTRACT: start() is deliberately not synchronising. The runtime loop task has not
    # taken its first step yet, so the component is STARTED and not yet RUNNING.
    assert blocking_component.status.state is State.STARTED
    assert blocking_component.calls == ["on_started"]

    await asyncio.wait_for(blocking_component.wait_until_started(), timeout=_TIMEOUT)

    assert blocking_component.status.state is State.RUNNING
    assert blocking_component.calls == ["on_started", "on_running"]


async def test_start_clears_the_stop_event(blocking_component: _RecordingComponent):
    blocking_component.stop_event.set()

    await blocking_component.start()

    assert not blocking_component.stop_event.is_set()


async def test_start_rejects_a_started_component(
    blocking_component: _RecordingComponent,
):
    await blocking_component.start()

    with pytest.raises(frmwrk_excs.ComponentAlreadyRunningError):
        await blocking_component.start()


async def test_start_rejects_a_running_component(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)

    with pytest.raises(frmwrk_excs.ComponentAlreadyRunningError):
        await blocking_component.start()


async def test_start_signal_error_rolls_back_to_initialized(
    component: _RecordingComponent,
):
    component.behaviours["on_started"] = _raises(
        sig_excs.ComponentStartError(message="cannot bind", detail={"port": 80}),
    )

    with pytest.raises(frmwrk_excs.ComponentStartError) as exc_info:
        await component.start()

    # CONTRACT: signal exceptions are part of the contract and get wrapped.
    assert "cannot bind" in exc_info.value.message
    assert exc_info.value.detail == {"port": 80}
    assert exc_info.value.__cause__ is None
    assert component.status.state is State.INITIALIZED
    assert component.status.error is None
    assert component._runtime_loop_task is None
    assert component.calls == ["on_started"]


# CONTRACT: an unhandled exception from a hook is reported as a ComponentFatalError, not
# raw. The error the caller catches is the very object the status now carries, so the
# failure has one description rather than two, and the exception that actually killed the
# component stays reachable as __cause__ for server side tracebacks.
async def test_start_unhandled_exception_goes_fatal_and_raises_a_fatal_error(
    component: _RecordingComponent,
):
    boom = ValueError("boom")
    component.behaviours["on_started"] = _raises(boom)

    with pytest.raises(frmwrk_excs.ComponentFatalError) as exc_info:
        await component.start()

    assert exc_info.value.__cause__ is boom
    assert exc_info.value.message == (
        "Failed to start the component test-component. An unhandled exception was "
        "raised. ValueError: boom"
    )
    assert exc_info.value.detail == {
        "type": "ValueError",
        "message": "boom",
        "phase": str(ComponentLifeCyclePhase.START),
    }
    assert component.status.state is State.FATAL
    assert component.status.error is exc_info.value
    assert component._runtime_loop_task is None
    assert [phase for _, phase in component.fatal_calls] == [
        ComponentLifeCyclePhase.START,
    ]
    # The hook still receives the original exception rather than the wrapper.
    assert component.fatal_calls[0][0] is boom


@pytest.mark.parametrize("state", _TERMINAL_STATES)
async def test_start_restarts_from_every_terminal_state(
    blocking_component: _RecordingComponent,
    state: State,
):
    # CONTRACT: start() is the restart path, no reset() required, and the transition to
    # STARTED clears any error left behind by the previous run.
    _force_state(blocking_component, state)

    await blocking_component.start()

    assert blocking_component.status.state is State.STARTED
    assert blocking_component.status.error is None

    await asyncio.wait_for(blocking_component.wait_until_started(), timeout=_TIMEOUT)

    assert blocking_component.status.state is State.RUNNING


async def test_start_reruns_every_hook_on_restart(component: _RecordingComponent):
    await component.start()
    await asyncio.wait_for(component.wait_until_stopped(), timeout=_TIMEOUT)
    assert component.calls == ["on_started", "on_running", "on_completed"]

    await component.start()
    await asyncio.wait_for(component.wait_until_stopped(), timeout=_TIMEOUT)

    assert component.calls == [
        "on_started",
        "on_running",
        "on_completed",
        "on_started",
        "on_running",
        "on_completed",
    ]


# CONTRADICTION (F6, accepted): start() only guards against STARTED/RUNNING, so calling
# it while STOPPING escapes as a bare AssertionError from the transition table rather
# than as a framework error. Documented as intended: invalid transitions are programmer
# error.
async def test_start_while_stopping_raises_assertion_error(
    component: _RecordingComponent,
):
    _force_state(component, State.STOPPING)

    with pytest.raises(AssertionError):
        await component.start()


# ---------------------------------------------------------------------------
# runtime loop
# ---------------------------------------------------------------------------


async def test_runtime_loop_runs_to_completion(component: _RecordingComponent):
    # CONTRACT: a finite unit of work is a first class component shape.
    await component.start()
    await asyncio.wait_for(component.wait_until_stopped(), timeout=_TIMEOUT)

    assert component.status.state is State.COMPLETED
    assert component.status.error is None
    assert component.calls == ["on_started", "on_running", "on_completed"]
    # CONTRACT: stop_event means "a stop was requested", so a natural completion leaves
    # it clear.
    assert not component.stop_event.is_set()


async def test_runtime_loop_skips_completion_when_a_stop_was_requested(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)

    await blocking_component.stop()
    await asyncio.wait_for(blocking_component.wait_until_stopped(), timeout=_TIMEOUT)

    assert "on_completed" not in blocking_component.calls
    assert blocking_component.status.state is State.STOPPED


async def test_runtime_loop_signal_error_transitions_to_errored(
    component: _RecordingComponent,
):
    component.behaviours["on_running"] = _raises(
        sig_excs.ComponentRuntimeError(message="lost connection", detail={"code": 7}),
    )

    await component.start()
    await asyncio.wait_for(component.wait_until_stopped(), timeout=_TIMEOUT)

    assert component.status.state is State.ERRORED
    assert component.calls == ["on_started", "on_running", "on_errored"]
    assert len(component.errored_with) == 1
    error = component.errored_with[0]
    assert isinstance(error, frmwrk_excs.ComponentRuntimeError)
    assert "lost connection" in error.message
    assert error.detail == {"code": 7}
    # The error handed to the hook is the same object recorded on the status.
    assert component.status.error is error
    assert component.fatal_calls == []


async def test_runtime_loop_errored_hook_failure_goes_fatal(
    component: _RecordingComponent,
):
    boom = RuntimeError("handler exploded")
    component.behaviours["on_running"] = _raises(
        sig_excs.ComponentRuntimeError(message="lost connection"),
    )
    component.behaviours["on_errored"] = _raises(boom)

    await component.start()
    await asyncio.wait_for(component.wait_until_stopped(), timeout=_TIMEOUT)

    assert component.status.state is State.FATAL
    assert isinstance(component.status.error, frmwrk_excs.ComponentFatalError)
    assert component.status.error.message == (
        "Failed to handle a runtime error within the component test-component. An "
        "unhandled exception was raised. RuntimeError: handler exploded"
    )
    assert [phase for _, phase in component.fatal_calls] == [
        ComponentLifeCyclePhase.ERROR,
    ]
    assert component.fatal_calls[0][0] is boom


async def test_runtime_loop_unhandled_exception_goes_fatal(
    component: _RecordingComponent,
):
    boom = ValueError("boom")
    component.behaviours["on_running"] = _raises(boom)

    await component.start()
    await asyncio.wait_for(component.wait_until_stopped(), timeout=_TIMEOUT)

    assert component.status.state is State.FATAL
    assert isinstance(component.status.error, frmwrk_excs.ComponentFatalError)
    assert component.status.error.message == (
        "Failed to run the component test-component. An unhandled exception was raised. "
        "ValueError: boom"
    )
    # The runtime loop has no caller to raise to, so the fatal error is recorded on the
    # status and never raised. Nothing chains the original onto it here.
    assert component.status.error.__cause__ is None
    assert component.calls == ["on_started", "on_running", "on_fatal"]
    assert [phase for _, phase in component.fatal_calls] == [
        ComponentLifeCyclePhase.RUNNING,
    ]


async def test_runtime_loop_completed_hook_failure_goes_fatal(
    component: _RecordingComponent,
):
    component.behaviours["on_completed"] = _raises(ValueError("boom"))

    await component.start()
    await asyncio.wait_for(component.wait_until_stopped(), timeout=_TIMEOUT)

    assert component.status.state is State.FATAL
    assert [phase for _, phase in component.fatal_calls] == [
        ComponentLifeCyclePhase.RUNNING,
    ]


# CONTRADICTION (F7): on_fatal() is the last resort handler. A component that raises
# from it must not have that exception escape the runtime loop task (where nobody
# retrieves it) and must not corrupt the status. The component stays FATAL carrying the
# ORIGINAL error, and on_fatal() is never re-entered. The secondary failure is recorded on
# the stored error as `fatal_hook_error` (surfacing it through to_json() is deferred).
async def test_runtime_loop_fatal_hook_failure_is_contained(
    component: _RecordingComponent,
):
    component.behaviours["on_running"] = _raises(ValueError("boom"))
    component.behaviours["on_fatal"] = _raises(RuntimeError("fatal handler exploded"))

    await component.start()
    await asyncio.wait_for(component.wait_until_stopped(), timeout=_TIMEOUT)
    await _settle()

    assert component.status.state is State.FATAL
    assert "ValueError: boom" in component.status.error.message
    # No recursion: on_fatal() is invoked exactly once.
    assert component.calls.count("on_fatal") == 1
    # The secondary failure from on_fatal() is recorded on the stored error rather than
    # lost. It cannot live on __cause__, which is reserved for the exception that killed
    # the component.
    assert isinstance(component.status.error.fatal_hook_error, RuntimeError)
    assert str(component.status.error.fatal_hook_error) == "fatal handler exploded"


# The raising life cycle methods chain the original exception onto __cause__, so a failing
# on_fatal() must not cost the caller that chain: the two failures occupy separate slots.
async def test_start_fatal_hook_failure_keeps_the_original_cause(
    component: _RecordingComponent,
):
    boom = ValueError("boom")
    component.behaviours["on_started"] = _raises(boom)
    component.behaviours["on_fatal"] = _raises(RuntimeError("fatal handler exploded"))

    with pytest.raises(frmwrk_excs.ComponentFatalError) as exc_info:
        await component.start()

    assert exc_info.value.__cause__ is boom
    assert isinstance(exc_info.value.fatal_hook_error, RuntimeError)
    assert str(exc_info.value.fatal_hook_error) == "fatal handler exploded"


# ---------------------------------------------------------------------------
# stop()
# ---------------------------------------------------------------------------


async def test_stop_transitions_through_stopping_to_stopped(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)
    observed: list[State] = []
    blocking_component.behaviours["on_stopped"] = lambda: observed.append(
        blocking_component.status.state,
    )

    await blocking_component.stop()

    assert observed == [State.STOPPING]
    assert blocking_component.status.state is State.STOPPED
    assert blocking_component.status.error is None
    assert blocking_component.stop_event.is_set()
    assert blocking_component.calls == ["on_started", "on_running", "on_stopped"]


async def test_stop_releases_a_component_blocked_on_the_stop_event(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)

    await blocking_component.stop()
    await asyncio.wait_for(blocking_component.wait_until_stopped(), timeout=_TIMEOUT)

    assert blocking_component.status.state is State.STOPPED
    assert "on_completed" not in blocking_component.calls


@pytest.mark.parametrize("state", _NON_RUNNING_STATES)
async def test_stop_rejects_every_non_running_state(
    component: _RecordingComponent,
    state: State,
):
    _force_state(component, state)

    with pytest.raises(frmwrk_excs.ComponentNotRunningError):
        await component.stop()

    assert component.status.state is state
    assert component.calls == []


# CONTRADICTION (F3): a refused stop currently strands the component in STOPPING, a state
# whose only outgoing edges are STOPPED and FATAL, so the component can never be
# restarted or reset and its runtime loop keeps running. Expected: roll back to RUNNING,
# mirroring how a refused start() rolls back to INITIALIZED.
async def test_stop_signal_error_rolls_back_to_running(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)
    blocking_component.behaviours["on_stopped"] = _raises(
        sig_excs.ComponentStopError(message="mid transaction", detail={"pending": 3}),
    )

    with pytest.raises(frmwrk_excs.ComponentStopError) as exc_info:
        await blocking_component.stop()

    assert "mid transaction" in exc_info.value.message
    assert exc_info.value.detail == {"pending": 3}
    assert blocking_component.status.state is State.RUNNING
    assert not blocking_component.stop_event.is_set()

    # The component is still live and can still be stopped afterwards.
    blocking_component.behaviours.pop("on_stopped")
    await blocking_component.stop()

    assert blocking_component.status.state is State.STOPPED


# REGRESSION (RUNNING-zombie): a refused stop must leave the component genuinely live even
# when on_stopped() suspends before raising. stop() must not release the parked
# on_running() until on_stopped() has accepted the stop. Otherwise an async on_stopped()
# that suspends after the wake signal lets the runtime loop drain on_running() to
# completion and clear its task, and the following refusal then rolls back to RUNNING with
# no live runtime loop task, an impossible state that also makes wait_until_stopped()
# report the component at rest. The suspension is modelled with _settle() so the
# interleaving is deterministic rather than timing dependent.
async def test_refused_stop_that_suspends_keeps_the_runtime_task_live(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)

    async def _yield_then_refuse() -> None:
        # Hand control to the runtime loop mid stop, then refuse. If stop() had already set
        # stop_event the parked on_running() would drain here and clear the runtime task.
        await _settle(3)
        raise sig_excs.ComponentStopError(message="still busy", detail={"pending": 1})

    blocking_component.behaviours["on_stopped"] = _yield_then_refuse

    with pytest.raises(frmwrk_excs.ComponentStopError):
        await blocking_component.stop()

    # The refusal restored RUNNING without ever raising the wake signal, and crucially the
    # runtime loop task is still live to keep driving on_running().
    assert blocking_component.status.state is State.RUNNING
    assert not blocking_component.stop_event.is_set()
    assert blocking_component._runtime_loop_task is not None
    assert not blocking_component._runtime_loop_task.done()

    # And it can still be stopped cleanly afterwards.
    blocking_component.behaviours.pop("on_stopped")
    await blocking_component.stop()
    await asyncio.wait_for(blocking_component.wait_until_stopped(), timeout=_TIMEOUT)

    assert blocking_component.status.state is State.STOPPED


# CONTRADICTION (F2): stop() transitions to FATAL without ever invoking on_fatal(),
# unlike start(), cancel() and the runtime loop. ComponentLifeCyclePhase.STOP is
# defined and currently unused, which is the evidence this is an omission.
async def test_stop_unhandled_exception_goes_fatal_and_calls_on_fatal(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)
    boom = ValueError("boom")
    blocking_component.behaviours["on_stopped"] = _raises(boom)

    with pytest.raises(frmwrk_excs.ComponentFatalError) as exc_info:
        await blocking_component.stop()

    assert exc_info.value.__cause__ is boom
    assert exc_info.value.message == (
        "Failed to stop the component test-component. An unhandled exception was "
        "raised. ValueError: boom"
    )
    assert exc_info.value.detail["phase"] == str(
        ComponentLifeCyclePhase.STOP,
    )
    assert blocking_component.status.state is State.FATAL
    assert blocking_component.status.error is exc_info.value
    assert [phase for _, phase in blocking_component.fatal_calls] == [
        ComponentLifeCyclePhase.STOP,
    ]
    assert blocking_component.fatal_calls[0][0] is boom


async def test_stop_twice_rejects_the_second_call(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)
    await blocking_component.stop()

    with pytest.raises(frmwrk_excs.ComponentNotRunningError):
        await blocking_component.stop()


# ---------------------------------------------------------------------------
# cancel()
# ---------------------------------------------------------------------------


# CONTRADICTION (F1): the runtime loop swallows CancelledError and returns, so the task
# completes normally, `_actually_cancelled` is never set, the CANCELLED transition never
# fires and on_cancelled() is never called. The component is stranded in RUNNING.
async def test_cancel_transitions_to_cancelled_and_calls_the_hook(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)

    await blocking_component.cancel()

    assert blocking_component.status.state is State.CANCELLED
    assert blocking_component.status.error is None
    assert blocking_component.calls == ["on_started", "on_running", "on_cancelled"]
    # CONTRACT: cancelling is not a stop request, so the event stays clear.
    assert not blocking_component.stop_event.is_set()


async def test_cancel_actually_cancels_the_runtime_loop_task(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)
    task = blocking_component._runtime_loop_task

    await blocking_component.cancel()

    assert task.done()
    assert task.cancelled()


async def test_cancel_skips_the_completed_hooks(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)

    await blocking_component.cancel()

    assert "on_completed" not in blocking_component.calls
    assert "on_stopped" not in blocking_component.calls


@pytest.mark.parametrize("state", _NON_RUNNING_STATES)
async def test_cancel_rejects_every_non_running_state(
    component: _RecordingComponent,
    state: State,
):
    _force_state(component, state)

    with pytest.raises(frmwrk_excs.ComponentNotRunningError):
        await component.cancel()

    assert component.status.state is state


async def test_cancel_hook_failure_goes_fatal_and_reraises(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)
    boom = ValueError("boom")
    blocking_component.behaviours["on_cancelled"] = _raises(boom)

    with pytest.raises(frmwrk_excs.ComponentFatalError) as exc_info:
        await blocking_component.cancel()

    assert exc_info.value.__cause__ is boom
    assert exc_info.value.message == (
        "Failed to cancel the component test-component. An unhandled exception was "
        "raised. ValueError: boom"
    )
    assert blocking_component.status.state is State.FATAL
    assert blocking_component.status.error is exc_info.value
    assert [phase for _, phase in blocking_component.fatal_calls] == [
        ComponentLifeCyclePhase.CANCEL,
    ]


# CONTRADICTION (F13, surfaced while writing these tests): stop_event is a signalling
# primitive set only by stop(); a component setting its own stop_event without going
# through stop() is unsupported. The framework degrades gracefully rather than corrupting
# state: the runtime loop keys its completion decision off the lifecycle state, not
# stop_event, so a self-set event just reads as a normal completion (-> COMPLETED). A
# subsequent cancel() then cleanly rejects the already-terminal component; it must never
# raise AttributeError, and the component must be at rest in a terminal state.
async def test_cancel_when_the_runtime_task_has_already_finished(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)
    blocking_component.stop_event.set()
    await asyncio.wait_for(blocking_component.wait_until_stopped(), timeout=_TIMEOUT)
    await _settle()

    try:
        await blocking_component.cancel()
    except frmwrk_excs.ComponentsFrameworkError:
        pass

    assert blocking_component.status.state in _TERMINAL_STATES


# ---------------------------------------------------------------------------
# wait_until_started() / wait_until_stopped()
# ---------------------------------------------------------------------------


async def test_wait_until_started_returns_once_running(
    blocking_component: _RecordingComponent,
):
    await blocking_component.start()

    await asyncio.wait_for(blocking_component.wait_until_started(), timeout=_TIMEOUT)

    assert blocking_component.status.state is State.RUNNING


@pytest.mark.parametrize("state", _TERMINAL_STATES)
async def test_wait_until_started_returns_on_a_terminal_state(
    component: _RecordingComponent,
    state: State,
):
    _force_state(component, state)

    await asyncio.wait_for(component.wait_until_started(), timeout=_TIMEOUT)


# CONTRADICTION (F8): a start() that fails with a signal error rolls the state back to
# INITIALIZED, which is one of the states wait_until_started() polls on, so any concurrent
# waiter busy-spins forever. It must return instead.
async def test_wait_until_started_returns_after_a_failed_start(
    component: _RecordingComponent,
):
    component.behaviours["on_started"] = _raises(
        sig_excs.ComponentStartError(message="cannot bind"),
    )
    waiter = asyncio.create_task(component.wait_until_started())
    await _settle()

    with pytest.raises(frmwrk_excs.ComponentStartError):
        await component.start()

    await asyncio.wait_for(waiter, timeout=_TIMEOUT)


async def test_wait_until_stopped_returns_immediately_when_never_started(
    component: _RecordingComponent,
):
    await asyncio.wait_for(component.wait_until_stopped(), timeout=_TIMEOUT)

    assert component.status.state is State.INITIALIZED


@pytest.mark.parametrize(
    "hook_behaviour",
    [None, "signal", "unhandled"],
)
async def test_wait_until_stopped_returns_on_every_terminal_exit(
    component: _RecordingComponent,
    hook_behaviour: str | None,
):
    if hook_behaviour == "signal":
        component.behaviours["on_running"] = _raises(sig_excs.ComponentRuntimeError())
    elif hook_behaviour == "unhandled":
        component.behaviours["on_running"] = _raises(ValueError("boom"))

    await component.start()
    await asyncio.wait_for(component.wait_until_stopped(), timeout=_TIMEOUT)

    assert component.status.state in _TERMINAL_STATES


async def test_wait_until_stopped_returns_after_a_cancel(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)
    await blocking_component.cancel()

    await asyncio.wait_for(blocking_component.wait_until_stopped(), timeout=_TIMEOUT)


# CONTRADICTION (F9): wait_until_stopped() catches CancelledError indiscriminately, so a
# cancellation aimed at the CALLER is swallowed and the waiter completes normally. Only
# the runtime task's own cancellation may be absorbed.
async def test_wait_until_stopped_propagates_the_callers_cancellation(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)
    waiter = asyncio.create_task(blocking_component.wait_until_stopped())
    await _settle()

    waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiter

    assert waiter.cancelled()


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", _TERMINAL_STATES)
def test_reset_returns_a_terminal_component_to_initialized(
    component: _RecordingComponent,
    state: State,
):
    _force_state(component, state)
    component.stop_event.set()

    component.reset()

    assert component.status.state is State.INITIALIZED
    assert component.status.error is None
    assert not component.stop_event.is_set()
    assert component._runtime_loop_task is None


def test_reset_is_idempotent(component: _RecordingComponent):
    component.reset()
    component.reset()

    assert component.status.state is State.INITIALIZED


async def test_reset_clears_the_runtime_loop_task(component: _RecordingComponent):
    await component.start()
    await asyncio.wait_for(component.wait_until_stopped(), timeout=_TIMEOUT)

    component.reset()

    assert component._runtime_loop_task is None
    assert component.status.state is State.INITIALIZED


# CONTRADICTION (F-conc): reset() is only legal from INITIALIZED or a terminal state.
# From STARTED it currently succeeds and orphans a live runtime loop task (which then
# happily transitions the freshly reset status back to RUNNING); from RUNNING and
# STOPPING it escapes as a bare AssertionError. It must refuse with a framework error and
# change nothing.
@pytest.mark.parametrize("state", [State.STARTED, State.RUNNING, State.STOPPING])
async def test_reset_refuses_a_live_component(
    blocking_component: _RecordingComponent,
    state: State,
):
    await blocking_component.start()
    if state is not State.STARTED:
        await asyncio.wait_for(
            blocking_component.wait_until_started(), timeout=_TIMEOUT
        )
    if state is State.STOPPING:
        blocking_component.status._transition_to_stopping()

    with pytest.raises(frmwrk_excs.ComponentAlreadyRunningError):
        blocking_component.reset()

    assert blocking_component.status.state is state
    assert blocking_component._runtime_loop_task is not None


# ---------------------------------------------------------------------------
# concurrency
# ---------------------------------------------------------------------------


# CONTRACT: lifecycle operations must be concurrency safe. The precondition guards are
# separated from their state changes by awaits, so overlapping calls must be serialized
# internally; exactly one wins and the loser gets a clean framework error.
async def test_concurrent_starts_leave_exactly_one_winner(
    blocking_component: _RecordingComponent,
):
    results = await asyncio.gather(
        blocking_component.start(),
        blocking_component.start(),
        return_exceptions=True,
    )

    failures = [result for result in results if isinstance(result, BaseException)]
    assert len(failures) == 1
    assert isinstance(failures[0], frmwrk_excs.ComponentAlreadyRunningError)
    assert blocking_component.calls.count("on_started") == 1


async def test_concurrent_stop_and_cancel_leave_exactly_one_winner(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)
    # Force the two operations to interleave by making the stop hook yield.
    blocking_component.behaviours["on_stopped"] = lambda: asyncio.sleep(0)

    results = await asyncio.gather(
        blocking_component.stop(),
        blocking_component.cancel(),
        return_exceptions=True,
    )

    failures = [result for result in results if isinstance(result, BaseException)]
    assert len(failures) == 1
    assert isinstance(failures[0], frmwrk_excs.ComponentNotRunningError)
    assert blocking_component.status.state in (State.STOPPED, State.CANCELLED)


async def test_concurrent_cancel_and_stop_leave_exactly_one_winner(
    blocking_component: _RecordingComponent,
):
    await _bring_to_running(blocking_component)
    blocking_component.behaviours["on_stopped"] = lambda: asyncio.sleep(0)

    results = await asyncio.gather(
        blocking_component.cancel(),
        blocking_component.stop(),
        return_exceptions=True,
    )

    failures = [result for result in results if isinstance(result, BaseException)]
    assert len(failures) == 1
    assert isinstance(failures[0], frmwrk_excs.ComponentNotRunningError)
    assert blocking_component.status.state in (State.STOPPED, State.CANCELLED)


# CONTRADICTION (F-lock): a component that finishes on_running() under its own steam
# while a stop() is in flight corrupts the status. stop() has already moved to STOPPING
# but does not set stop_event until it has finished, so the resuming runtime loop takes
# the completion branch and attempts STOPPING -> COMPLETED, which is not a legal edge.
# The AssertionError is then caught by the loop's own `except Exception`, dragging the
# component to FATAL, and stop()'s trailing STOPPING -> STOPPED fails in turn.
# The releasing of on_running() is driven from inside on_stopped() so the interleaving is
# deterministic rather than timing dependent.
async def test_stop_racing_natural_completion_does_not_corrupt_the_status(
    component: _RecordingComponent,
):
    release = asyncio.Event()
    component.behaviours["on_running"] = release.wait

    async def _release_then_yield() -> None:
        release.set()
        # Hand control to the runtime loop while stop() is still mid flight.
        await _settle(3)

    component.behaviours["on_stopped"] = _release_then_yield
    await _bring_to_running(component)

    results = await asyncio.gather(component.stop(), return_exceptions=True)
    await asyncio.wait_for(component.wait_until_stopped(), timeout=_TIMEOUT)
    await _settle()

    assert not any(isinstance(result, AssertionError) for result in results)
    assert component.status.state in _TERMINAL_STATES
    assert component.status.state is not State.FATAL


# ---------------------------------------------------------------------------
# ComponentMetadata
# ---------------------------------------------------------------------------


def test_metadata_normalizes_a_fully_populated_declaration():
    class _Component(ComponentMetadata):
        label = "my-component"
        name = "My Component"
        description = "does things"
        version = "1.2.3"
        compatible_framework_version = ">=1.0,<2.0"
        authors = {"someone"}
        component_dependencies = {"other-component>=2.0"}

    _Component._validate_metadata()

    assert _Component.label == "my-component"
    assert _Component.name == "My Component"
    assert _Component.version == version.Version("1.2.3")
    assert isinstance(_Component.version, version.Version)
    assert _Component.compatible_framework_version == specifiers.SpecifierSet(
        ">=1.0,<2.0",
    )
    assert _Component.authors == {"someone"}
    assert len(_Component.component_dependencies) == 1
    dependency = next(iter(_Component.component_dependencies))
    assert isinstance(dependency, requirements.Requirement)
    assert dependency.name == "other-component"
    # Seeded empty, populated later by the loader from the component's pyproject.toml.
    assert _Component.third_party_dependencies == set()


def test_metadata_defaults_name_to_label_and_empties_optional_collections():
    class _Component(ComponentMetadata):
        label = "minimal"

    _Component._validate_metadata()

    assert _Component.name == "minimal"
    assert _Component.description == ""
    assert _Component.version is None
    assert _Component.compatible_framework_version is None
    assert _Component.authors == set()
    assert _Component.component_dependencies == set()


def test_metadata_missing_label_raises_and_names_the_defining_module():
    class _Component(ComponentMetadata):
        pass

    with pytest.raises(
        frmwrk_excs.MissingComponentConfigurationParameterError,
    ) as exc_info:
        _Component._validate_metadata()

    assert "label" in exc_info.value.message
    assert __file__ in exc_info.value.message


def test_metadata_empty_label_raises():
    class _Component(ComponentMetadata):
        label = ""

    with pytest.raises(frmwrk_excs.EmptyComponentLabelError) as exc_info:
        _Component._validate_metadata()

    assert __file__ in exc_info.value.message


def test_metadata_wrong_attribute_type_raises_naming_the_parameter():
    class _Component(ComponentMetadata):
        label = "bad-authors"
        authors = 12345

    with pytest.raises(
        frmwrk_excs.InvalidComponentConfigurationParameterTypeError,
    ) as exc_info:
        _Component._validate_metadata()

    assert "authors" in exc_info.value.message


def test_metadata_invalid_version_raises():
    class _Component(ComponentMetadata):
        label = "bad-version"
        version = "not a version"

    with pytest.raises(frmwrk_excs.InvalidComponentVersionError) as exc_info:
        _Component._validate_metadata()

    assert "not a version" in exc_info.value.message


def test_metadata_invalid_framework_version_specifier_raises():
    class _Component(ComponentMetadata):
        label = "bad-specifier"
        compatible_framework_version = "!!!"

    with pytest.raises(frmwrk_excs.InvalidFrameworkVersionSpecifierError) as exc_info:
        _Component._validate_metadata()

    assert "bad-specifier" in exc_info.value.message


def test_metadata_invalid_dependency_entry_raises():
    class _Component(ComponentMetadata):
        label = "bad-dependency"
        component_dependencies = {"=="}

    with pytest.raises(
        frmwrk_excs.InvalidComponentDependencyVersionSpecifierError,
    ) as exc_info:
        _Component._validate_metadata()

    assert "==" in exc_info.value.message


# CONTRACT: _validate_metadata() is idempotent. It normalizes the class attributes in
# place into the packaging objects the framework consumes, so a second pass no longer
# sees the declared strings; it reads them back in their declared form to stay valid.
# This matters because a subclass of an already validated component class is validated
# again by __init_subclass__ against the values it inherited.
def test_metadata_validation_is_idempotent():
    class _Component(ComponentMetadata):
        label = "idempotent"
        version = "1.0.0"
        compatible_framework_version = ">=0.1.0a1"
        component_dependencies = {"some-component==1.0.0"}

    _Component._validate_metadata()
    _Component._validate_metadata()

    assert _Component.version == version.Version("1.0.0")
    assert _Component.compatible_framework_version == specifiers.SpecifierSet(
        ">=0.1.0a1"
    )
    assert {str(entry) for entry in _Component.component_dependencies} == {
        "some-component==1.0.0"
    }


# A subclass inherits the parent's normalized attributes and is validated again by
# __init_subclass__, so the normalized values have to survive that second pass.
def test_a_subclass_of_a_validated_component_keeps_the_inherited_metadata():
    class _Component(ComponentMetadata):
        label = "parent"
        version = "1.0.0"
        compatible_framework_version = ">=0.1.0a1"

    _Component._validate_metadata()

    class _Subcomponent(_Component):
        label = "child"

    _Subcomponent._validate_metadata()

    assert _Subcomponent.version == version.Version("1.0.0")
    assert _Subcomponent.compatible_framework_version == specifiers.SpecifierSet(
        ">=0.1.0a1"
    )


# ---------------------------------------------------------------------------
# Life cycle exception set
# ---------------------------------------------------------------------------


# A domain that overrides the life cycle exception set, standing in for BaseListener and
# friends. The message templates render "$C_LOWER$" as "widget", so a message that was
# formatted twice is visible as a repeated prefix.
class _WidgetsFrameworkError(frmwrk_excs.ComponentsFrameworkError):
    code = "WIDGETS_FRAMEWORK_ERROR"

    _COMPONENT_TYPE = "widget"


class _WidgetStartError(frmwrk_excs.ComponentStartError, _WidgetsFrameworkError):
    code = "WIDGET_START_ERROR"


class _WidgetStopError(frmwrk_excs.ComponentStopError, _WidgetsFrameworkError):
    code = "WIDGET_STOP_ERROR"


class _WidgetRuntimeError(frmwrk_excs.ComponentRuntimeError, _WidgetsFrameworkError):
    code = "WIDGET_RUNTIME_ERROR"


class _WidgetFatalError(frmwrk_excs.ComponentFatalError, _WidgetsFrameworkError):
    code = "WIDGET_FATAL_ERROR"


class _WidgetNotRunningError(
    frmwrk_excs.ComponentNotRunningError,
    _WidgetsFrameworkError,
):
    code = "WIDGET_NOT_RUNNING_ERROR"


class _WidgetAlreadyRunningError(
    frmwrk_excs.ComponentAlreadyRunningError,
    _WidgetsFrameworkError,
):
    code = "WIDGET_ALREADY_RUNNING_ERROR"


class _WidgetComponent(_RecordingComponent):
    _component_life_cycle_exceptions = ComponentLifeCycleExceptions(
        start=_WidgetStartError,
        stop=_WidgetStopError,
        runtime=_WidgetRuntimeError,
        fatal=_WidgetFatalError,
        not_running=_WidgetNotRunningError,
        already_running=_WidgetAlreadyRunningError,
    )

    def __str__(self) -> str:
        return "test-widget"


@pytest.fixture
def widget_component() -> _WidgetComponent:
    return _WidgetComponent()


def test_life_cycle_exception_set_defaults_to_the_generic_component_errors():
    instance = _RecordingComponent()

    exceptions = instance._component_life_cycle_exceptions

    assert exceptions.start is frmwrk_excs.ComponentStartError
    assert exceptions.stop is frmwrk_excs.ComponentStopError
    assert exceptions.runtime is frmwrk_excs.ComponentRuntimeError
    assert exceptions.fatal is frmwrk_excs.ComponentFatalError
    assert exceptions.not_running is frmwrk_excs.ComponentNotRunningError
    assert exceptions.already_running is frmwrk_excs.ComponentAlreadyRunningError


# REGRESSION: the domain error used to be produced by the domain base class catching the
# generic component error and re-raising, which fed an already formatted message back
# through a second template and nested the prefix ("Failed to start the widget X. Failed
# to start the component X. ..."). The life cycle now raises the domain class directly, so
# the prefix is applied exactly once.
async def test_start_error_formats_the_message_exactly_once(
    widget_component: _WidgetComponent,
):
    widget_component.behaviours["on_started"] = _raises(
        sig_excs.ComponentStartError(message="raw signal message."),
    )

    with pytest.raises(_WidgetStartError) as exc_info:
        await widget_component.start()

    message = exc_info.value.message
    assert message.count("Failed to start the") == 1
    assert "Failed to start the component" not in message
    assert message == "Failed to start the widget test-widget. raw signal message."


async def test_stop_error_formats_the_message_exactly_once():
    widget_component = _WidgetComponent()
    widget_component.behaviours["on_running"] = widget_component.stop_event.wait
    widget_component.behaviours["on_stopped"] = _raises(
        sig_excs.ComponentStopError(message="raw signal message."),
    )
    await _bring_to_running(widget_component)

    with pytest.raises(_WidgetStopError) as exc_info:
        await widget_component.stop()

    message = exc_info.value.message
    assert message.count("Failed to stop the") == 1
    assert "Failed to stop the component" not in message
    assert message == "Failed to stop the widget test-widget. raw signal message."


async def test_runtime_error_formats_the_message_exactly_once(
    widget_component: _WidgetComponent,
):
    widget_component.behaviours["on_running"] = _raises(
        sig_excs.ComponentRuntimeError(message="raw signal message."),
    )

    await widget_component.start()
    await _settle()

    assert widget_component.status.state is State.ERRORED
    error = widget_component.status.error
    assert isinstance(error, _WidgetRuntimeError)
    assert error.message.count("Failed to run the") == 1
    assert error.message == "Failed to run the widget test-widget. raw signal message."


async def test_fatal_error_is_raised_as_the_domain_error(
    widget_component: _WidgetComponent,
):
    boom = ValueError("boom")
    widget_component.behaviours["on_started"] = _raises(boom)

    with pytest.raises(_WidgetFatalError) as exc_info:
        await widget_component.start()

    assert exc_info.value.__cause__ is boom
    assert exc_info.value.message == (
        "Failed to start the widget test-widget. An unhandled exception was raised. "
        "ValueError: boom"
    )
    assert widget_component.status.error is exc_info.value


# The state guards carry no `error_message`, so they cannot nest, but they must still be
# raised as the domain class rather than the generic component class.
async def test_state_guards_raise_the_domain_error(
    widget_component: _WidgetComponent,
):
    with pytest.raises(_WidgetNotRunningError):
        await widget_component.stop()

    with pytest.raises(_WidgetNotRunningError):
        await widget_component.cancel()

    widget_component.behaviours["on_running"] = widget_component.stop_event.wait
    await _bring_to_running(widget_component)

    with pytest.raises(_WidgetAlreadyRunningError):
        await widget_component.start()


async def test_start_error_raises_from_none(
    widget_component: _WidgetComponent,
):
    origin = OSError("address already in use")
    signal_error = sig_excs.ComponentStartError(message="could not bind.")
    signal_error.__cause__ = origin
    widget_component.behaviours["on_started"] = _raises(signal_error)

    with pytest.raises(_WidgetStartError) as exc_info:
        await widget_component.start()

    assert exc_info.value.__cause__ is None


async def test_stop_error_raises_from_none():
    widget_component = _WidgetComponent()
    widget_component.behaviours["on_running"] = widget_component.stop_event.wait
    signal_error = sig_excs.ComponentStopError(message="could not flush.")
    widget_component.behaviours["on_stopped"] = _raises(signal_error)
    await _bring_to_running(widget_component)

    with pytest.raises(_WidgetStopError) as exc_info:
        await widget_component.stop()

    assert exc_info.value.__cause__ is None


# A domain that overrides only some slots keeps the generic error for the rest. This is
# the shape BaseAgentGeneratorBuildStep uses: a build step specific runtime error, generic
# component errors everywhere else.
async def test_partial_exception_set_falls_back_to_the_generic_errors():
    class _PartialComponent(_RecordingComponent):
        _component_life_cycle_exceptions = ComponentLifeCycleExceptions(
            runtime=_WidgetRuntimeError,
        )

    instance = _PartialComponent()
    instance.behaviours["on_started"] = _raises(
        sig_excs.ComponentStartError(message="raw signal message."),
    )

    with pytest.raises(frmwrk_excs.ComponentStartError) as exc_info:
        await instance.start()

    assert not isinstance(exc_info.value, _WidgetStartError)
    assert exc_info.value.message == (
        "Failed to start the component test-component. raw signal message."
    )

    # The failed signal start rolled back to INITIALIZED, so the component can be started
    # again directly.
    instance.behaviours["on_started"] = _raises(ValueError("boom"))

    with pytest.raises(frmwrk_excs.ComponentFatalError) as fatal_exc_info:
        await instance.start()

    assert not isinstance(fatal_exc_info.value, _WidgetFatalError)
    assert fatal_exc_info.value.message == (
        "Failed to start the component test-component. An unhandled exception was "
        "raised. ValueError: boom"
    )
